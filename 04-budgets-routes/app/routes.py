"""The route table: which route a request starts on, each route's model and budget, and where a refusal escalates.

A route is a policy directory under policy/ (route-policy.json and profile.json) plus the entry in routes.json that
names its model, its context limit and what it reserves for the answer. budget.input is computed, never typed (R-16).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import impl

POLICY = Path(__file__).resolve().parents[1] / "policy"


def table(which: str | None = None) -> dict[str, Any]:
    return json.loads(impl.path("routes.json", which).read_text(encoding="utf-8"))


def default(which: str | None = None) -> str:
    return table(which)["default"]


def budget(route: str, which: str | None = None) -> dict[str, Any]:
    entry = table(which)["routes"][route]
    return {"input": entry["model_context_limit"] - entry["reserved_output"],
            "reserved_output": entry["reserved_output"], "margin_percent": entry["margin_percent"]}


def model(route: str, which: str | None = None) -> str:
    return table(which)["routes"][route]["model"]


def policy(route: str, name: str) -> Any:
    return json.loads((POLICY / route / name).read_text(encoding="utf-8"))


def next_route(route: str, refusal_reason: str, which: str | None = None) -> str | None:
    """Where the application rebuilds the request after this route refused for this reason, or None to stop."""
    return table(which).get("escalate", {}).get(route, {}).get(refusal_reason)
