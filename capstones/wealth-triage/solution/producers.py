"""The route's producers: policy, the client profile, the ledger, the risk screen, the market-data vendor, the knowledge
base, the capability policy, and the chat session. Each proposes; the route decides."""

from __future__ import annotations

import json
import re
from typing import Any

import common
from common import Request, batch, item

Facts = dict[str, str]
GOVERNING = dict(authority="governing", trust="verified", conflict_policy="governs", lineage="verbatim", injection_risk="none")
AMOUNT = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d{4,})(?:\.\d+)?\b")


def advice_policy(route: str) -> dict[str, Any]:
    meta, body = common.front_matter(common.policy(route, "instructions.md"))
    cmeta, contract = common.front_matter(common.policy(route, "contract.md"))
    return batch("advice-policy", "policy", [
        item(id=f"policy:{route}", slot="governance.instructions", source=f"app:policy/{route}/instructions.md", source_version=meta["version"], freshness=meta["updated"], body=body, **GOVERNING),
        item(id=f"contract:{route}", slot="governance.output_contract", source=f"app:policy/{route}/contract.md", source_version=cmeta["version"], freshness=cmeta["updated"], body=contract, **GOVERNING),
    ])


def client_state(request: Request) -> dict[str, Any]:
    """The client profile: mandate, risk tier, KYC. Protected by the route. No account number, IBAN or card: the model
    never needs them, and a reply that held one would fail the screen anyway."""
    c = common.clients()[request.client]
    return batch("client-state", "state", [item(
        id=f"client:{request.client}", slot="state.user", source=f"clients-db:{request.client}", source_version=str(c["version"]), authority="state", trust="verified",
        freshness=request.asked_at, scope={"tenant": common.TENANT, "user": request.client}, conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"Client {c['name']} ({request.client}): {c['mandate']} mandate, {c['risk_tier']} risk tier, KYC {c['kyc']}, country {c['country']}.")])


def ledger(request: Request) -> tuple[dict[str, Any], Facts]:
    """Settled positions and cash from the custodian: the system of record. Each position asserts its fact."""
    book = common.ledger()
    acct = book["accounts"][request.account]
    positions = "; ".join(f"{p['symbol']} ({p['name']}): {p['units']} units settled, average cost {p['avg_cost']:.2f}" for p in acct["positions"])
    lid = f"ledger:{request.account}"
    facts = {lid: f"position.{p['symbol']}" for p in acct["positions"] if p["symbol"] == "ACME"}
    return batch("ledger", "state", [item(
        id=lid, slot="state.task", source=f"custodian-ledger:{request.account}", source_version=str(acct["version"]), authority="state", trust="verified",
        freshness=book["as_of"], scope={"tenant": common.TENANT, "task": request.account}, conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"Ledger for the account as of {book['as_of']}: cash {acct['cash']:.2f} {acct['currency']}. Positions: {positions}.")]), facts


def risk_level(request: Request) -> tuple[str, list[str]]:
    """The deterministic risk screen the application runs before assembly: signals from the session and the message."""
    signals = []
    if request.device == "new":
        signals.append("session from a device this account has not used before")
    amounts = [float(a.replace(",", "")) for a in AMOUNT.findall(request.question)]
    if any(a >= 5000 for a in amounts):
        signals.append("the message names an amount of 5,000 or more")
    if any(w in request.question.lower() for w in ("transfer", "withdraw", "send money", "move money")):
        signals.append("the message asks about moving money")
    if request.device == "new" and len(signals) >= 2:
        return "critical", signals
    return ("elevated" if signals else "low"), signals


def risk_screen(request: Request) -> dict[str, Any]:
    """Application-written state (R-8): the risk level and its signals, so the model reads a decision, not raw signals."""
    level, signals = risk_level(request)
    return batch("risk-screen", "state", [item(
        id=f"risk:{request.session}", slot="state.task", source=f"risk-screen:{request.session}", source_version="rules/v2", authority="state", trust="verified",
        freshness=request.asked_at, scope={"tenant": common.TENANT, "task": request.account}, conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"Risk screen for this session: {level}." + (" Signals: " + "; ".join(signals) + "." if signals else " No signals."))])


def market_data(request: Request) -> tuple[dict[str, Any], Facts]:
    """The vendor's quotes and its estimate of the account's positions, as observations (R-10, R-15). The estimate asserts
    the position fact and loses to the ledger by the route's precedence."""
    m = common.market()
    acct = common.ledger()["accounts"][request.account]
    symbols = sorted({p["symbol"] for p in acct["positions"]})
    items = [item(id=f"quote:{s}", slot="evidence.tool_results", source=f"market-data:quotes/{s}", source_version=m["as_of"], authority="observation", trust="unverified",
                  freshness=m["as_of"], scope={"tenant": common.TENANT, "task": request.account}, conflict_policy="governs", lineage="verbatim", injection_risk="untrusted_content",
                  body=f"Last quote {s}: {m['quotes'][s]:.2f} GBP at {m['as_of']} (vendor feed, may be delayed).") for s in symbols]
    facts = {}
    for v in m["vendor_positions"].get(request.account, []):
        vid = f"vendor-position:{request.account}:{v['symbol']}"
        items.append(item(id=vid, slot="evidence.tool_results", source=f"market-data:positions/{request.account}/{v['symbol']}", source_version=m["as_of"], authority="observation",
                          trust="unverified", freshness=m["as_of"], scope={"tenant": common.TENANT, "task": request.account}, conflict_policy="governs", lineage="verbatim",
                          injection_risk="untrusted_content", body=f"Vendor estimate: {v['symbol']} {v['units']} units ({v['basis']})."))
        facts[vid] = f"position.{v['symbol']}"
    return batch("market-data", "retrieval", items), facts


def kb_search(request: Request, top_k: int) -> dict[str, Any]:
    return batch("kb-search", "retrieval", [item(
        id=chunk.id, slot="evidence.knowledge", source=f"kb:{chunk.article}", source_version=chunk.version, authority="reference_only", trust="verified",
        freshness=chunk.updated, relevance=score, lineage="verbatim", injection_risk="untrusted_content", body=chunk.text,
    ) for chunk, score in common.bm25(request.question)[:top_k]])


def capability_policy(request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    """The only producer of governance.capabilities (R-15): the portal's proposals granted by the client's mandate and the
    risk screen, the rest reported capability_not_allowed. The grant names the offered ids."""
    rules, proposed = common.capabilities_policy(), common.tools()
    mandate = common.clients()[request.client]["mandate"]
    level, _ = risk_level(request)
    order = rules["risk_order"]
    items, excluded = [], []
    for spec in sorted(proposed["tools"], key=lambda s: s["name"]):
        cap_id = f"cap:{spec['name']}"
        rule = rules["grants"].get(spec["name"])
        if rule is None or mandate not in rule["mandates"] or order.index(level) > order.index(rule["max_risk"]):
            excluded.append({"item_id": cap_id, "reason": "capability_not_allowed", "stage": "producer"})
            continue
        items.append(item(id=cap_id, slot="governance.capabilities", source=f"capability-policy:{proposed['server']}/{spec['name']}",
                          source_version=f"{rules['allow_list_version']}+{proposed['version']}", freshness=request.asked_at,
                          body=json.dumps({"name": spec["name"], "description": rule["description"], "input_schema": spec["input_schema"]}, sort_keys=True), **GOVERNING))
    grant = {"policy_producer": rules["policy_producer"], "allow_list_version": rules["allow_list_version"], "allowed_ids": sorted(i["id"] for i in items)}
    return batch(rules["policy_producer"], "capability_policy", items, excluded), grant


def chat_session(request: Request) -> dict[str, Any]:
    scope, source, items = {"session": request.session}, f"portal-chat:{request.session}", []
    for n, turn in enumerate(request.turns, start=1):
        generated = turn.role == "assistant"
        items.append(item(id=f"turn:{request.session}:{n:04d}", slot="interaction.history", source=source, source_version="1",
                          authority="untrusted" if generated else "user", lineage="generated" if generated else "verbatim", trust="unverified",
                          freshness=turn.at, scope=scope, injection_risk="untrusted_content", body=turn.text))
    items.append(item(id=f"turn:{request.session}:{len(request.turns) + 1:04d}", slot="interaction.query", source=source, source_version="1", authority="user",
                      lineage="verbatim", trust="unverified", freshness=request.asked_at, scope=scope, injection_risk="untrusted_content", body=request.question))
    return batch("chat-session", "interaction", items)
