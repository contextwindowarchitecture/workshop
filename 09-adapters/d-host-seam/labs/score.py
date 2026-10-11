"""Your trace scorer: dropped_high_severity(document, trace) -> the ids of prior findings (slot interaction.memory, body
beginning "high ·") that fitting left out (reason over_budget). It reads the snapshot for the bodies and the trace for
the decisions, and never a model's output. Lab 2 in the README."""

from __future__ import annotations

from typing import Any


def dropped_high_severity(document: dict[str, Any], trace: dict[str, Any]) -> list[str]:
    raise NotImplementedError("labs/score.py: dropped_high_severity")
