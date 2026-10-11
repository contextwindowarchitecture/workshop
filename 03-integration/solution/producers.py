"""Step 3 of the migration: every piece of the old prompt becomes items with an authority and a source.

    app-policy          governance.instructions   policy/instructions.md, versioned
    accounts-db         state.user                the workspace's plan and the user's role, read at request time
    memory-store        interaction.memory        live memories; expired and revoked ones reported, not sent
    help-center-search  evidence.knowledge        one scored item per retrieved paragraph
    chat-session        interaction.history       every prior turn; the route decides how many fit
                        interaction.query         the question

accounts_db and memory_store also return the fact each item asserts, so context.py can declare conflict groups; the
assembler never reads prose to find a contradiction (R-11).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from request import Request, accounts, corpus, memories
from solution.context import instant

POLICY = Path(__file__).resolve().parent / "policy"
Facts = dict[str, str]  # item id -> fact key from the route policy's facts


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
    items = [
        item(id=plan_id, source=f"accounts-db:workspaces/{request.tenant}", source_version=str(workspace["version"]),
             scope={"tenant": request.tenant},
             body=f"Workspace {workspace['name']} is on the {workspace['plan']} plan, billed {workspace['billing']}, since "
                  f"{workspace['plan_since']}. {workspace['seats']} seats. Data region: {workspace['region']}.", **common),
        item(id=f"account:{request.tenant}:{request.user}", source=f"accounts-db:users/{request.user}",
             source_version=str(member["version"]), scope={"tenant": request.tenant, "user": request.user},
             body=f"{member['name']} is a workspace {member['role']}" + (" and a billing admin." if member["billing_admin"] else ", not a billing admin."),
             **common),
    ]
    return batch("accounts-db", "state", items), {plan_id: "plan"}


def memory_store(request: Request) -> tuple[dict[str, Any], Facts]:
    ignores_user = "memory-store-ignores-user" in request.faults
    asked = instant(request.asked_at)
    items, excluded, facts = [], [], {}
    for memory in memories():
        if memory["workspace"] != request.tenant or (memory["user"] != request.user and not ignores_user):
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
    items = []
    for chunk, score in corpus.bm25(request.question)[:top_k]:
        items.append(item(
            id=chunk.id, slot="evidence.knowledge", source=f"help-center:{chunk.article}", source_version=chunk.version,
            authority="reference_only", trust="verified", freshness=chunk.updated, relevance=score,
            lineage="verbatim", injection_risk="untrusted_content", body=chunk.text,
        ))
    return batch("help-center-search", "retrieval", items)


def turn_id(session: str, n: int) -> str:
    return f"turn:{session}:{n:04d}"


def chat_session(request: Request) -> dict[str, Any]:
    scope, source, items = {"session": request.session}, f"chat:{request.session}", []
    for n, turn in enumerate(request.turns, start=1):
        generated = turn.role == "assistant"
        items.append(item(
            id=turn_id(request.session, n), slot="interaction.history", source=source, source_version="1",
            authority="untrusted" if generated else "user", lineage="generated" if generated else "verbatim",
            trust="unverified", freshness=turn.at, scope=scope, injection_risk="untrusted_content", body=turn.text,
        ))
    items.append(item(
        id=turn_id(request.session, len(request.turns) + 1), slot="interaction.query", source=source, source_version="1",
        authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at, scope=scope,
        injection_risk="untrusted_content", body=request.question,
    ))
    return batch("chat-session", "interaction", items)
