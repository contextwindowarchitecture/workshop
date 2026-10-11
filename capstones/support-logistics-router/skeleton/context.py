"""Your freeze: snapshot(request, route, tier, budget_input=None) -> dict, assemble(document), conflict_groups(facts).
The snapshot's budget comes from common.budget(tier), its profile and route policy from policy/<route>/, and its conflicts
from the facts the producers return. budget_input overrides budget.input for one attempt (the orchestrator uses it)."""

from __future__ import annotations

from typing import Any

from cwa import AssemblyResult

from common import Request


def conflict_groups(facts: dict[str, str]) -> list[dict[str, Any]]:
    raise NotImplementedError("skeleton/context.py: conflict_groups")


def snapshot(request: Request, route: str, tier: str, budget_input: int | None = None) -> dict[str, Any]:
    raise NotImplementedError("skeleton/context.py: snapshot")


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    raise NotImplementedError("skeleton/context.py: assemble")
