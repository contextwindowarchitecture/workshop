"""Freeze one request under one profile and one renderer. Everything else about the snapshot is fixed, which is what
makes profiles comparable: same items, same route policy, same budget, same clock; only placement and rendering vary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cwa import AssemblyResult, Snapshot
from cwa import assemble as cwa_assemble

import impl
from app import producers
from request import Request, Turn

POLICY = Path(__file__).resolve().parents[1] / "policy"
BUDGET = {"input": 7168, "reserved_output": 1024, "margin_percent": 15}
TOP_K = 6
BLOCKS, MESSAGES = "cwa-message-blocks/v1", "cwa-messages/v1"


def route_policy() -> dict[str, Any]:
    return json.loads((POLICY / "route-policy.json").read_text(encoding="utf-8"))


def profiles(which: str | None = None) -> dict[str, dict[str, Any]]:
    return {p["id"]: p for p in json.loads(impl.path("profiles.json", which).read_text(encoding="utf-8"))["profiles"]}


def conflict_groups(facts: dict[str, str]) -> list[dict[str, Any]]:
    claims: dict[str, list[str]] = {}
    for item_id, fact in facts.items():
        claims.setdefault(fact, []).append(item_id)
    return [{"id": f"fact:{fact}", "kind": "fact", "fact": fact, "items": sorted(ids)} for fact, ids in sorted(claims.items()) if len(ids) >= 2]


def snapshot(request: Request, profile: dict[str, Any], renderer: str = BLOCKS) -> dict[str, Any]:
    account_batch, account_facts = producers.accounts_db(request)
    memory_batch, memory_facts = producers.memory_store(request)
    return {
        "assembly_time": request.asked_at,
        "scope": {"tenant": request.tenant, "user": request.user, "session": request.session},
        "budget": dict(BUDGET),
        "profile": profile,
        "route_policy": route_policy(),
        "tokenizer": "estimate-utf8/v1",
        "renderer": renderer,
        "batches": [producers.app_policy(), account_batch, memory_batch, producers.help_center_search(request, TOP_K), producers.chat_session(request)],
        "conflicts": conflict_groups(account_facts | memory_facts),
    }


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    return cwa_assemble(Snapshot.from_json(document))


def turns_of(conversation: dict[str, Any]) -> list[Request]:
    """A frozen conversation as the sequence of requests the application made: turn n carries the n-1 exchanges before
    it as history and asks exchange n's question. Timestamps advance a minute per message."""
    from datetime import datetime, timedelta, timezone

    start = datetime.fromisoformat(conversation["started_at"].replace("Z", "+00:00"))
    stamp = lambda i: (start + timedelta(minutes=i)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    requests, history = [], []
    for n, exchange in enumerate(conversation["exchanges"]):
        requests.append(Request(user=conversation["user"], session=conversation["session"], asked_at=stamp(2 * n), question=exchange["q"], turns=tuple(history)))
        history += [Turn("user", exchange["q"], stamp(2 * n)), Turn("assistant", exchange["a"], stamp(2 * n + 1))]
    return requests
