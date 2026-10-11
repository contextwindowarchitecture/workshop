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
    orders, order_facts = producers.orders_db(request)
    notes, note_facts = producers.crm_notes(request)
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
        "batches": [producers.support_policy(route), producers.customer_state(request), producers.ticket_state(request, route), orders, notes,
                    producers.kb_search(request, table["retrieval"]["top_k"]), producers.web_chat(request)],
        "conflicts": conflict_groups(order_facts | note_facts),
    }


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    return cwa_assemble(Snapshot.from_json(document))
