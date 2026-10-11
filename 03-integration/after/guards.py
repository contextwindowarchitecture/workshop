"""Step 6: the "never" sentences in the old prompt, enforced outside the model (R-5).

    no_unverified_prices(reply, evidence_bodies) -> Decision
        every currency amount in the reply appears in an evidence body the assembler included
    only_the_signed_in_workspace(reply, request) -> Decision
        the reply names no workspace other than request.tenant's
    check(reply, request, evidence_bodies) -> list[Decision]

Keep the sentences in policy/instructions.md: they are guidance. These are the invariants, and they run on the
reply against what was actually sent, whatever the model was told.
"""

from __future__ import annotations

from dataclasses import dataclass

from request import Request


@dataclass(frozen=True)
class Decision:
    ok: bool
    reason: str


def no_unverified_prices(reply: str, evidence_bodies: list[str]) -> Decision:
    raise NotImplementedError("Step 6: see MIGRATION.md")


def only_the_signed_in_workspace(reply: str, request: Request) -> Decision:
    raise NotImplementedError("Step 6: see MIGRATION.md")


def check(reply: str, request: Request, evidence_bodies: list[str]) -> list[Decision]:
    return [no_unverified_prices(reply, evidence_bodies), only_the_signed_in_workspace(reply, request)]
