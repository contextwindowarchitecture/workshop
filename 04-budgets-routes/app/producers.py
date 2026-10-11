"""The W3a producers, with one addition: the retrieval producer attaches a reviewed, precomputed summary as a variant.

Variants are computed before any request and cached by the SHA-256 of the paragraph (R-18): summaries/summaries.json
holds one per paragraph, and the review list says which of them a person has read against the paragraph and
approved. Only approved summaries become variants. An unreviewed summary is a sentence the model would read as
evidence, written by another model, that nobody checked.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import impl
from request import Request, accounts, corpus, memories

HERE = Path(__file__).resolve().parents[1]
SUMMARIES = HERE / "summaries" / "summaries.json"
Facts = dict[str, str]


def instant(text: str):
    from datetime import datetime
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def item(**fields: Any) -> dict[str, Any]:
    return {"token_budget": None, "variants": [], "conflict_policy": "defers", "eligibility": "route-policy", **fields}


def batch(producer_id: str, kind: str, items: list[dict[str, Any]], excluded: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"producer": {"id": producer_id, "kind": kind}, "items": items, "excluded": excluded or []}


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def approved(which: str | None = None) -> set[str]:
    return set(json.loads(impl.path("reviewed.json", which).read_text(encoding="utf-8"))["approved"])


def variants_for(chunk: corpus.Chunk, which: str | None = None) -> list[dict[str, str]]:
    """The reviewed summary of this paragraph, looked up by content hash, as a variant with its own id."""
    if chunk.id not in approved(which):
        return []
    entry = json.loads(SUMMARIES.read_text(encoding="utf-8")).get(content_hash(chunk.text))
    if not entry:
        return []
    return [{"id": f"{chunk.id}~{entry['suffix']}", "body": entry["body"], "method": entry["method"], "lineage": entry["lineage"]}]


def app_policy() -> dict[str, Any]:
    meta, body = corpus.front_matter((HERE / "policy" / "instructions.md").read_text(encoding="utf-8"))
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


def help_center_search(request: Request, top_k: int, which: str | None = None) -> dict[str, Any]:
    items = []
    for chunk, score in corpus.bm25(request.question)[:top_k]:
        items.append(item(
            id=chunk.id, slot="evidence.knowledge", source=f"help-center:{chunk.article}", source_version=chunk.version,
            authority="reference_only", trust="verified", freshness=chunk.updated, relevance=score,
            lineage="verbatim", injection_risk="untrusted_content", body=chunk.text, variants=variants_for(chunk, which),
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
