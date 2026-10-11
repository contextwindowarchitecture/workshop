"""The route's producers: policy, three state producers, the CRM notes as memory with precomputed variants, the
knowledge base, and the web chat. Each proposes; the route decides."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

import common
from common import Request, batch, item

Facts = dict[str, str]
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def redact(text: str) -> tuple[str, bool]:
    """Contact details out of anything that goes to the model. The model never needs them; the agent who reads the CRM does."""
    clean = _EMAIL.sub("[email redacted]", _PHONE.sub("[phone redacted]", text))
    return clean, clean != text


def support_policy(route: str) -> dict[str, Any]:
    meta, body = common.front_matter(common.policy(route, "instructions.md"))
    cmeta, contract = common.front_matter((common.POLICY / "output-contract.md").read_text(encoding="utf-8"))
    common_fields = dict(authority="governing", trust="verified", conflict_policy="governs", lineage="verbatim", injection_risk="none")
    return batch("support-policy", "policy", [
        item(id=f"policy:{route}", slot="governance.instructions", source=f"app:policy/{route}/instructions.md", source_version=meta["version"], freshness=meta["updated"], body=body, **common_fields),
        item(id="contract:json-reply", slot="governance.output_contract", source="app:policy/output-contract.md", source_version=cmeta["version"], freshness=cmeta["updated"], body=contract, **common_fields),
    ])


def customer_state(request: Request) -> dict[str, Any]:
    c = common.customers()[request.customer]
    return batch("customer-state", "state", [item(
        id=f"customer:{request.customer}", slot="state.user", source=f"customers-db:{request.customer}", source_version=str(c["version"]),
        authority="state", trust="verified", freshness=request.asked_at, scope={"tenant": common.TENANT, "user": request.customer},
        conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"Customer {c['name']} ({request.customer}), {c['tier']}, country {c['country']}.",  # no contact details: the model never needs them
    )])


def ticket_state(request: Request, route: str) -> dict[str, Any]:
    t = common.tickets()[request.ticket]
    return batch("ticket-state", "state", [item(
        id=f"ticket:{request.ticket}", slot="state.task", source=f"tickets-db:{request.ticket}", source_version=t["updated_at"],
        authority="state", trust="verified", freshness=request.asked_at, scope={"tenant": common.TENANT, "task": request.ticket},
        conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"Ticket {request.ticket} for order {t['order']}: stage {t['stage']}, routed as {route}, return requested {t['return_requested']}, "
             f"label sent {t['label_sent']}, refund {t['refund_status']}, attempts {t['attempts']}.",
    )])


def orders_db(request: Request) -> tuple[dict[str, Any], Facts]:
    order_id = common.tickets()[request.ticket]["order"]
    o = common.orders()[order_id]
    items = ", ".join(f"{i['name']} ({i['price']:.2f})" for i in o["items"])
    body = (f"Order {order_id} placed {o['placed']}, {o['shipping']} shipping, status {o['status']}"
            + (f", delivered {o['delivered_at']}" if o["delivered_at"] else "") + f". Items: {items}.")
    oid = f"order:{order_id}"
    return batch("orders-db", "state", [item(
        id=oid, slot="state.task", source=f"orders-db:{order_id}", source_version=str(o["version"]), authority="state", trust="verified",
        freshness=request.asked_at, scope={"tenant": common.TENANT, "task": request.ticket}, conflict_policy="governs", lineage="extracted",
        injection_risk="none", body=body,
    )]), {oid: f"delivery_status:{order_id}"}


def crm_notes(request: Request) -> tuple[dict[str, Any], Facts]:
    ignores_customer = "crm-ignores-customer" in request.faults
    asked = common.instant(request.asked_at)
    items, excluded, facts = [], [], {}
    for note in common.crm_notes():
        if note["customer"] != request.customer and not ignores_customer:
            continue
        expires = (common.instant(note["at"]) + timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if common.instant(expires) <= asked:
            excluded.append({"item_id": note["id"], "reason": "expired", "stage": "producer"})
            continue
        body, redacted = redact(note["text"])
        summary, _ = redact(note["summary"])
        items.append(item(
            id=note["id"], slot="interaction.memory", source=note["id"], source_version="1", authority="generated", trust="unverified",
            freshness=note["at"], expires=expires, scope={"tenant": common.TENANT, "user": note["customer"]},
            lineage="redacted" if redacted else "verbatim", injection_risk="untrusted_content", body=body,
            variants=[{"id": f"{note['id']}~summary", "body": summary, "method": "agent-written summary", "lineage": "summarised"}],
        ))
        if "fact" in note:
            facts[note["id"]] = note["fact"]
    return batch("crm-notes", "memory", items, excluded), facts


def kb_search(request: Request, top_k: int) -> dict[str, Any]:
    return batch("kb-search", "retrieval", [item(
        id=chunk.id, slot="evidence.knowledge", source=f"kb:{chunk.article}", source_version=chunk.version, authority="reference_only",
        trust="verified", freshness=chunk.updated, relevance=score, lineage="verbatim", injection_risk="untrusted_content", body=chunk.text,
    ) for chunk, score in common.bm25(request.question)[:top_k]])


def web_chat(request: Request) -> dict[str, Any]:
    scope, source, items = {"session": request.session}, f"chat:{request.session}", []
    for n, turn in enumerate(request.turns, start=1):
        generated = turn.role == "assistant"
        items.append(item(id=f"turn:{request.session}:{n:04d}", slot="interaction.history", source=source, source_version="1",
                          authority="untrusted" if generated else "user", lineage="generated" if generated else "verbatim", trust="unverified",
                          freshness=turn.at, scope=scope, injection_risk="untrusted_content", body=turn.text))
    items.append(item(id=f"turn:{request.session}:{len(request.turns) + 1:04d}", slot="interaction.query", source=source, source_version="1",
                      authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at, scope=scope,
                      injection_risk="untrusted_content", body=request.question))
    return batch("web-chat", "interaction", items)
