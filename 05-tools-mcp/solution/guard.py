"""Lab A, solved: the guard. Every tool call the model asks for passes through here before the server sees it (R-5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jsonschema

from capability_policy import Grant, policy


@dataclass(frozen=True)
class Decision:
    approved: bool
    reason: str


def authorize(name: str, arguments: Any, granted: dict[str, Grant], scope: dict[str, str], which: str | None = None) -> Decision:
    if name not in granted:
        never = policy(which).get("never", {})
        why = f": {never[name]}" if name in never else ""
        return Decision(False, f"{name} is not offered on this turn{why}")
    grant = granted[name]
    if not isinstance(arguments, dict):
        return Decision(False, f"the arguments for {name} are not a JSON object")
    problems = sorted(e.message for e in jsonschema.Draft202012Validator(grant.input_schema).iter_errors(arguments))
    if problems:
        return Decision(False, f"the arguments do not match {name}'s schema: {'; '.join(problems)}")
    for argument, key in grant.scope.items():
        if arguments.get(argument) != scope.get(key):
            return Decision(False, f"{argument}={arguments.get(argument)!r} is not the signed-in {key} ({scope.get(key)})")
    return Decision(True, f"offered as {grant.cap_id}; the arguments match the schema and the request's scope")
