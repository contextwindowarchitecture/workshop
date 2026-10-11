"""Your screens, run on the parsed draft outside the model (R-5):

    actions_were_offered(actions, granted) -> Decision          every action's tool is in the set the final request offered (cap ids without "cap:")
    prescription_guard(actions, request) -> Decision            a refill names an active chart medicine, this patient, and the clinician prescribes
    vitals_match_state(objective, current, stale) -> Decision   the objective records the current BP and none the route decided against
    citations_were_sent(citations, sent) -> Decision            every cited paragraph id was in the final request
    check(parsed, request, route, sent, granted, current_bp, stale_bp) -> list[Decision]   citations on every route; the other three on scribe

A failing decision makes the orchestrator withhold the draft and route the encounter to clinician review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from common import Request


@dataclass(frozen=True)
class Decision:
    name: str
    ok: bool
    reason: str


def actions_were_offered(actions: list[dict[str, Any]], granted: set[str]) -> Decision:
    raise NotImplementedError("skeleton/guards.py: actions_were_offered")


def prescription_guard(actions: list[dict[str, Any]], request: Request) -> Decision:
    raise NotImplementedError("skeleton/guards.py: prescription_guard")


def vitals_match_state(objective: str, current: str | None, stale: list[str]) -> Decision:
    raise NotImplementedError("skeleton/guards.py: vitals_match_state")


def citations_were_sent(citations: list[str], sent: set[str]) -> Decision:
    raise NotImplementedError("skeleton/guards.py: citations_were_sent")


def check(parsed: dict[str, Any], request: Request, route: str, sent: set[str], granted: set[str], current_bp: str | None, stale_bp: list[str]) -> list[Decision]:
    decisions = [citations_were_sent(parsed.get("citations", []), sent)]
    if route == "scribe":
        actions = parsed.get("actions") or []
        decisions += [actions_were_offered(actions, granted), prescription_guard(actions, request), vitals_match_state(parsed.get("objective", ""), current_bp, stale_bp)]
    return decisions
