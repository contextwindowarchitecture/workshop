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
    policy = common.policy(route, "route-policy.json")
    vitals, vital_facts = producers.telemetry(request)
    notes, note_facts = producers.ehr_notes(request)
    budget = common.budget(tier)
    if budget_input is not None:
        budget = {**budget, "input": budget_input}
    batches = [producers.clinical_policy(route), producers.ehr_chart(request), vitals, producers.clinician_state(request), notes,
               producers.guidelines(request, table["retrieval"]["top_k"]), producers.ambient_scribe(request)]
    document: dict[str, Any] = {
        "assembly_time": request.asked_at,
        "scope": request.scope,
        "budget": budget,
        "profile": common.policy(route, "profile.json"),
        "route_policy": policy,
        "tokenizer": table["tokenizer"],
        "renderer": table["renderer"],
        "batches": batches,
        "conflicts": conflict_groups(vital_facts | note_facts),
    }
    if "capability-policy" in policy["producers"]:
        caps, grant = producers.capability_policy(request)
        batches.append(caps)
        document["capabilities"] = grant
    return document


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    return cwa_assemble(Snapshot.from_json(document))
