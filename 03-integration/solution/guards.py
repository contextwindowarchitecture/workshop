"""Step 6 of the migration: the "never" sentences in the old prompt, enforced outside the model (R-5).

The instructions still say "never quote a price that does not appear in the articles" and "never reveal another
workspace's details". Those sentences stay: they are language guidance. These functions are the invariants: they run on
the model's reply, against what the assembler actually sent, and they do not care how the model was asked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from request import Request, accounts

_AMOUNT = re.compile(r"(?:[$€£]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:dollars|euros|pounds|USD|EUR|GBP)\b)", re.IGNORECASE)


@dataclass(frozen=True)
class Decision:
    ok: bool
    reason: str


def _normalise(amount: str) -> str:
    return re.sub(r"[\s,]", "", amount.lower())


def no_unverified_prices(reply: str, evidence_bodies: list[str]) -> Decision:
    """Every amount in the reply must appear in an evidence body the assembler included."""
    seen = {_normalise(m) for body in evidence_bodies for m in _AMOUNT.findall(body)}
    for amount in _AMOUNT.findall(reply):
        if _normalise(amount) not in seen:
            return Decision(False, f"the reply quotes {amount.strip()}, which appears in no article that was sent")
    return Decision(True, "every amount in the reply appears in the evidence that was sent")


def only_the_signed_in_workspace(reply: str, request: Request) -> Decision:
    """The reply names no other workspace."""
    db = accounts()
    for workspace_id, workspace in db["workspaces"].items():
        if workspace_id != request.tenant and (workspace["name"].lower() in reply.lower() or workspace_id in reply):
            return Decision(False, f"the reply mentions {workspace['name']}, which is not the signed-in workspace")
    return Decision(True, "the reply names no other workspace")


def check(reply: str, request: Request, evidence_bodies: list[str]) -> list[Decision]:
    return [no_unverified_prices(reply, evidence_bodies), only_the_signed_in_workspace(reply, request)]
