"""Lab A: the guard. Every tool call the model asks for passes through authorize() before the server sees it (R-5).

Write it until `CWA_W5_IMPL=labs uv run pytest tests/test_lab_a_guard.py` passes. Four checks, in this order, each
returning Decision(False, reason) when it fails:

1. The tool was offered on this turn: `name in granted`. If not, say so; if the policy's "never" list names it,
   append that reason, because the model will read your words as state next turn and should learn why.
2. The arguments are a JSON object.
3. The arguments match the tool's input schema: `jsonschema.Draft202012Validator(grant.input_schema).iter_errors`.
4. Every argument the grant's scope rule names equals the request's scope value for that key: `grant.scope` maps an
   argument name to a scope key, so {"workspace": "tenant"} means arguments["workspace"] == scope["tenant"].

Return Decision(True, ...) only when all four hold. The model's wording plays no part; only the call and the
application's own state do.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from capability_policy import Grant


@dataclass(frozen=True)
class Decision:
    approved: bool
    reason: str


def authorize(name: str, arguments: Any, granted: dict[str, Grant], scope: dict[str, str], which: str | None = None) -> Decision:
    raise NotImplementedError("Lab A: see the module docstring")
