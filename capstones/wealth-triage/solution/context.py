"""Freeze one request on one route and one budget tier; declare the conflict groups the producers' facts imply."""

from __future__ import annotations

from typing import Any

from cwa import AssemblyResult, Snapshot
from cwa import assemble as cwa_assemble

import common
from common import Request
from solution import producers


def conflict_groups(facts: dict[str, str]) -> list[dict[str, Any]]:
    claims: dict[str, list[str]] = {}
    for item_id, fact in facts.items():
        claims.setdefault(fact, []).append(item_id)
    return [{"id": f"fact:{fact}", "kind": "fact", "fact": fact, "items": sorted(ids)} for fact, ids in sorted(claims.items()) if len(ids) >= 2]


def snapshot(request: Request, route: str, tier: str, budget_input: int | None = None) -> dict[str, Any]:
    table = common.routes()
    book, book_facts = producers.ledger(request)
    market, market_facts = producers.market_data(request)
    caps, grant = producers.capability_policy(request)
    budget = common.budget(tier)
    if budget_input is not None:
        budget = {**budget, "input": budget_input}
    return {
        "assembly_time": request.asked_at,
        "scope": request.scope,
        "budget": budget,
        "profile": common.policy(route, "profile.json"),
        "route_policy": common.policy(route, "route-policy.json"),
        "tokenizer": table["tokenizer"],
        "renderer": table["renderer"],
        "batches": [producers.advice_policy(route), producers.client_state(request), book, producers.risk_screen(request), market,
                    producers.kb_search(request, table["retrieval"]["top_k"]), caps, producers.chat_session(request)],
        "conflicts": conflict_groups(book_facts | market_facts),
        "capabilities": grant,
    }


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    return cwa_assemble(Snapshot.from_json(document))
