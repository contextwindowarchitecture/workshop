"""Your mapping from a refusal to a host outcome: host_outcome(document, trace) -> {"sandbox": "start" | "not started",
"route", "comment" (None when the sandbox starts; otherwise text written from the trace: the reason, the recovery action
in the host's words, what was left out for budget, the budget and policy version), "span" (attributes with cwa.refused,
and on a refusal cwa.refused.reason and cwa.recovery.action)}. The README's Lab 3 says what each field is for."""

from __future__ import annotations

from typing import Any


def host_outcome(document: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("labs/outcome.py: host_outcome")
