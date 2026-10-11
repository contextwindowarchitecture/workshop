"""Step 2 and step 5: freeze one request's context into a snapshot, and assemble it.

    snapshot(request) -> dict      snapshot.schema.json: assembly_time, scope, budget, profile, route_policy,
                                   tokenizer, renderer, batches, conflicts
    assemble(document) -> AssemblyResult
    reserved_output() -> int
    budget() -> dict               input = model_context_limit - reserved_output (R-16), reserved_output, margin_percent
    conflict_groups(facts) -> list one fact group per fact that two or more items assert (R-11)

policy/ needs three files you write: route-policy.json, profile.json and assembly.json. MIGRATION.md lists every
field. The solution's versions are a reference, not a template to copy blind: every number in them is a decision.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cwa import AssemblyResult

from request import Request


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def reserved_output() -> int:
    raise NotImplementedError("Step 5: see MIGRATION.md")


def budget() -> dict[str, Any]:
    raise NotImplementedError("Step 5: see MIGRATION.md")


def conflict_groups(facts: dict[str, str]) -> list[dict[str, Any]]:
    raise NotImplementedError("Step 3: see MIGRATION.md")


def snapshot(request: Request) -> dict[str, Any]:
    raise NotImplementedError("Step 2: see MIGRATION.md")


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    raise NotImplementedError("Step 2: see MIGRATION.md")
