"""Freeze one request's context for one route, and assemble it. The same producers run for every route; what differs
is the route policy, the profile and the budget, and so what fits."""

from __future__ import annotations

from typing import Any

from cwa import AssemblyResult, Snapshot
from cwa import assemble as cwa_assemble

from app import producers, routes
from request import Request


def conflict_groups(facts: dict[str, str]) -> list[dict[str, Any]]:
    claims: dict[str, list[str]] = {}
    for item_id, fact in facts.items():
        claims.setdefault(fact, []).append(item_id)
    return [{"id": f"fact:{fact}", "kind": "fact", "fact": fact, "items": sorted(ids)}
            for fact, ids in sorted(claims.items()) if len(ids) >= 2]


def snapshot(request: Request, route: str, which: str | None = None, budget_input: int | None = None) -> dict[str, Any]:
    table = routes.table(which)
    account_batch, account_facts = producers.accounts_db(request)
    memory_batch, memory_facts = producers.memory_store(request)
    budget = routes.budget(route, which)
    if budget_input is not None:
        budget = {**budget, "input": budget_input}
    return {
        "assembly_time": request.asked_at,
        "scope": {"tenant": request.tenant, "user": request.user, "session": request.session},
        "budget": budget,
        "profile": routes.policy(route, "profile.json"),
        "route_policy": routes.policy(route, "route-policy.json"),
        "tokenizer": table["tokenizer"],
        "renderer": table["renderer"],
        "batches": [
            producers.app_policy(),
            account_batch,
            memory_batch,
            producers.help_center_search(request, table["retrieval"]["top_k"], which),
            producers.chat_session(request),
        ],
        "conflicts": conflict_groups(account_facts | memory_facts),
    }


def assemble(document: dict[str, Any], tokenizers: dict[str, Any] | None = None) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    return cwa_assemble(Snapshot.from_json(document, tokenizers=tokenizers) if tokenizers else Snapshot.from_json(document))
