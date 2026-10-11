"""The screens that run on the parsed draft, outside the model (R-5): every action was offered, a refill is of a
medicine active on the chart and asked for by a prescriber, the objective records the vitals the route decided on,
and citations name guideline paragraphs that were sent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import common
from common import Request

BP = re.compile(r"\b(\d{2,3}/\d{2,3})\b")


@dataclass(frozen=True)
class Decision:
    name: str
    ok: bool
    reason: str


def actions_were_offered(actions: list[dict[str, Any]], granted: set[str]) -> Decision:
    for a in actions:
        if a.get("tool") not in granted:
            never = common.capabilities_policy().get("never", {})
            why = f": {never[a['tool']]}" if a.get("tool") in never else ""
            return Decision("actions_were_offered", False, f"the draft calls {a.get('tool')}, which was not offered on this route{why}")
    return Decision("actions_were_offered", True, f"{len(actions)} action(s), all offered")


def prescription_guard(actions: list[dict[str, Any]], request: Request) -> Decision:
    clinician = common.clinicians()[request.clinician]
    active = {m["name"].lower() for m in common.patients()[request.patient]["medications"] if m["status"] == "active"}
    for a in actions:
        if a.get("tool") != "order_prescription_refill":
            continue
        if not clinician["prescriber"]:
            return Decision("prescription_guard", False, f"{clinician['name']} is not a prescriber; no refill can be queued")
        medication = str(a.get("arguments", {}).get("medication", "")).lower()
        if medication not in active:
            return Decision("prescription_guard", False, f"the draft queues a refill of {medication or '?'}, which is not an active medicine on the chart")
        if a.get("arguments", {}).get("patient") != request.patient:
            return Decision("prescription_guard", False, "the refill names another patient")
    return Decision("prescription_guard", True, "every refill is of an active chart medicine, queued by a prescriber for this patient")


def vitals_match_state(objective: str, current: str | None, stale: list[str]) -> Decision:
    found = set(BP.findall(objective))
    if current and current not in found:
        return Decision("vitals_match_state", False, f"the objective does not record the current blood pressure {current}")
    wrong = sorted(found & set(stale))
    if wrong:
        return Decision("vitals_match_state", False, f"the objective records {wrong[0]}, a reading the route decided against")
    return Decision("vitals_match_state", True, f"the objective records the current reading{' ' + current if current else ''} and no stale one")


def citations_were_sent(citations: list[str], sent: set[str]) -> Decision:
    missing = [c for c in citations if c not in sent]
    if missing:
        return Decision("citations_were_sent", False, f"cites {missing}, which the request did not contain")
    return Decision("citations_were_sent", True, f"{len(citations)} citation(s), all sent")


def check(parsed: dict[str, Any], request: Request, route: str, sent: set[str], granted: set[str], current_bp: str | None, stale_bp: list[str]) -> list[Decision]:
    decisions = [citations_were_sent(parsed.get("citations", []), sent)]
    if route == "scribe":
        actions = parsed.get("actions") or []
        decisions += [actions_were_offered(actions, granted), prescription_guard(actions, request), vitals_match_state(parsed.get("objective", ""), current_bp, stale_bp)]
    return decisions
