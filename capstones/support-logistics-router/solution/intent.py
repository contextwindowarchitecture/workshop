"""Intent classification, run by the application before assembly. Deterministic rules here; a classifier model can
replace them behind the same contract: text in, route id and what matched out, computed before the snapshot (R-23)."""

from __future__ import annotations

from dataclasses import dataclass

import common


@dataclass(frozen=True)
class Intent:
    route: str
    matched: str | None


def classify(text: str) -> Intent:
    rules = common.intents()
    lowered = text.lower()
    for route, phrases in rules["routes"].items():
        for phrase in phrases:
            if phrase in lowered:
                return Intent(route, phrase)
    return Intent(rules["fallback"], None)
