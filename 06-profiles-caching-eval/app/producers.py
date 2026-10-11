"""W3a's producers, unchanged: the item set is fixed, and only placement varies in this module."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from request import Request, accounts, corpus, memories

POLICY = Path(__file__).resolve().parents[1] / "policy"
Facts = dict[str, str]


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def item(**fields: Any) -> dict[str, Any]:
    return {"token_budget": None, "variants": [], "conflict_policy": "defers", "eligibility": "route-policy", **fields}


def batch(producer_id: str, kind: str, items: list[dict[str, Any]], excluded: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"producer": {"id": producer_id, "kind": kind}, "items": items, "excluded": excluded or []}


def app_policy() -> dict[str, Any]:
    meta, body = corpus.front_matter((POLICY / "instructions.md").read_text(encoding="utf-8"))
    return batch("app-policy", "policy", [item(
        id="policy:instructions", slot="governance.instructions", source="app:policy/instructions.md",
        source_version=meta["version"], authority="governing", trust="verified", freshness=meta["updated"],
        conflict_policy="governs", lineage="verbatim", injection_risk="none", body=body,
    )])


def accounts_db(request: Request) -> tuple[dict[str, Any], Facts]:
    db = accounts()
    workspace, member = db["workspaces"][request.tenant], db["users"][request.user]
    common = dict(slot="state.user", authority="state", trust="verified", freshness=request.asked_at,
                  conflict_policy="governs", lineage="extracted", injection_risk="none")
    plan_id = f"account:{request.tenant}:plan"
    return batch("accounts-db", "state", [
        item(id=plan_id, source=f"accounts-db:workspaces/{request.tenant}", source_version=str(workspace["version"]),
             scope={"tenant": request.tenant},
             body=f"Workspace {workspace['name']} is on the {workspace['plan']} plan, billed {workspace['billing']}, since "
                  f"{workspace['plan_since']}. {workspace['seats']} seats. Data region: {workspace['region']}.", **common),
        item(id=f"account:{request.tenant}:{request.user}", source=f"accounts-db:users/{request.user}",
             source_version=str(member["version"]), scope={"tenant": request.tenant, "user": request.user},
             body=f"{member['name']} is a workspace {member['role']}" + (" and a billing admin." if member["billing_admin"] else ", not a billing admin."),
             **common),
    ]), {plan_id: "plan"}


def memory_store(request: Request) -> tuple[dict[str, Any], Facts]:
    asked = instant(request.asked_at)
    items, excluded, facts = [], [], {}
    for memory in memories():
        if memory["workspace"] != request.tenant or memory["user"] != request.user:
            continue
        if "revoked_by" in memory:
            excluded.append({"item_id": memory["id"], "reason": "revoked", "stage": "producer"})
            continue
        if instant(memory["expires"]) <= asked:
            excluded.append({"item_id": memory["id"], "reason": "expired", "stage": "producer"})
            continue
        items.append(item(
            id=memory["id"], slot="interaction.memory", source=memory["from_turn"], source_version="1",
            authority="generated", trust="unverified", freshness=memory["saved_at"], expires=memory["expires"],
            scope={"tenant": memory["workspace"], "user": memory["user"]}, lineage="summarised",
            injection_risk="untrusted_content", body=memory["text"],
        ))
        if "fact" in memory:
            facts[memory["id"]] = memory["fact"]
    return batch("memory-store", "memory", items, excluded), facts


def help_center_search(request: Request, top_k: int) -> dict[str, Any]:
    return batch("help-center-search", "retrieval", [item(
        id=chunk.id, slot="evidence.knowledge", source=f"help-center:{chunk.article}", source_version=chunk.version,
        authority="reference_only", trust="verified", freshness=chunk.updated, relevance=score,
        lineage="verbatim", injection_risk="untrusted_content", body=chunk.text,
    ) for chunk, score in corpus.bm25(request.question)[:top_k]])


def chat_session(request: Request) -> dict[str, Any]:
    scope, source, items = {"session": request.session}, f"chat:{request.session}", []
    for n, turn in enumerate(request.turns, start=1):
        generated = turn.role == "assistant"
        items.append(item(
            id=f"turn:{request.session}:{n:04d}", slot="interaction.history", source=source, source_version="1",
            authority="untrusted" if generated else "user", lineage="generated" if generated else "verbatim",
            trust="unverified", freshness=turn.at, scope=scope, injection_risk="untrusted_content", body=turn.text,
        ))
    items.append(item(
        id=f"turn:{request.session}:{len(request.turns) + 1:04d}", slot="interaction.query", source=source, source_version="1",
        authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at, scope=scope,
        injection_risk="untrusted_content", body=request.question,
    ))
    return batch("chat-session", "interaction", items)
