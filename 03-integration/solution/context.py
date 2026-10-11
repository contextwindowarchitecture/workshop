"""Step 2 of the migration: freeze one request's context into a snapshot, and assemble it.

The snapshot holds everything that can change the request: the producers' batches, the conflict groups the application
declares, the route policy, the profile, the budget, the tokenizer and renderer, the request's scope and the clock.
assemble() reads nothing else and calls no model (R-23).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from cwa import AssemblyResult, Snapshot
from cwa import assemble as cwa_assemble

from request import Request

POLICY = Path(__file__).resolve().parent / "policy"


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def policy(name: str) -> Any:
    return json.loads((POLICY / name).read_text(encoding="utf-8"))


def reserved_output() -> int:
    return policy("assembly.json")["reserved_output"]


def budget() -> dict[str, Any]:
    """budget.input is the model's context limit less what the route reserves for the answer (R-16)."""
    settings = policy("assembly.json")
    return {"input": settings["model_context_limit"] - settings["reserved_output"],
            "reserved_output": settings["reserved_output"], "margin_percent": settings["margin_percent"]}


def conflict_groups(facts: dict[str, str]) -> list[dict[str, Any]]:
    """One fact group per fact that two or more items assert. The route's facts decide each group by producer
    precedence; the assembler never compares the bodies (R-11)."""
    claims: dict[str, list[str]] = {}
    for item_id, fact in facts.items():
        claims.setdefault(fact, []).append(item_id)
    return [{"id": f"fact:{fact}", "kind": "fact", "fact": fact, "items": sorted(ids)}
            for fact, ids in sorted(claims.items()) if len(ids) >= 2]


def snapshot(request: Request) -> dict[str, Any]:
    from solution import producers  # late import: producers import instant from here

    settings = policy("assembly.json")
    account_batch, account_facts = producers.accounts_db(request)
    memory_batch, memory_facts = producers.memory_store(request)
    return {
        "assembly_time": request.asked_at,
        "scope": {"tenant": request.tenant, "user": request.user, "session": request.session},
        "budget": budget(),
        "profile": policy("profile.json"),
        "route_policy": policy("route-policy.json"),
        "tokenizer": settings["tokenizer"],
        "renderer": settings["renderer"],
        "batches": [
            producers.app_policy(),
            account_batch,
            memory_batch,
            producers.help_center_search(request, settings["retrieval"]["top_k"]),
            producers.chat_session(request),
        ],
        "conflicts": conflict_groups(account_facts | memory_facts),
    }


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    return cwa_assemble(Snapshot.from_json(document))
