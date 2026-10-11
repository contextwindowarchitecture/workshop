"""Your route selector. Contract: classify(text) -> Intent(route, matched), computed by the application before any
snapshot is frozen. data/intents.json holds keyword rules you may use; a classifier model may replace them later behind
the same contract. The routes table maps the intent to a route."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    route: str
    matched: str | None


def classify(text: str) -> Intent:
    raise NotImplementedError("skeleton/intent.py: classify")
