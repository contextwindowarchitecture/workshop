"""What the host does with each refusal: the mapping a product owner signs off on, in one place.

A refusal is an outcome of a valid snapshot, not an error. Each one tells the application something specific, and the
application decides what the user sees, what gets retried, and what goes to a person (R-12, R-17). This table is the
fullsend integration's state diagram applied to the account agent; W9 module D studies the original.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Outcome:
    action: str  # retry-larger-route | precompute-and-retry | needs-info | requires-manual-review | answer-without-evidence
    user_message: str
    operator_note: str


OUTCOMES: dict[tuple[str, str | None], Outcome] = {
    ("protected_content_over_budget", None): Outcome("retry-larger-route", "One moment, this needs a bit more room.", "escalate to the large route; alert if that refuses too"),
    ("slot_floor_over_budget", None): Outcome("retry-larger-route", "One moment, this needs a bit more room.", "escalate; review the floor if it recurs"),
    ("evidence_required", "request_context"): Outcome("needs-info", "I couldn't find anything in the help centre about that. Could you rephrase, or contact support@fernway.example?", "nothing retrievable; no retry"),
    ("evidence_required", "precompute_summary"): Outcome("precompute-and-retry", "One moment.", "an evidence item had no variant; queue summarisation, retry once"),
    ("evidence_required", "retrieve_narrower"): Outcome("precompute-and-retry", "One moment.", "evidence was shed for budget; retry with a narrower query"),
    ("conflict_unresolved", None): Outcome("requires-manual-review", "I have conflicting information about your account and don't want to guess. Support will follow up.", "open a ticket with the conflict groups from the trace"),
    ("required_slot_missing", None): Outcome("requires-manual-review", "Something went wrong on our side.", "an application bug: a required producer emitted nothing"),
    ("protected_slot_unplaced", None): Outcome("requires-manual-review", "Something went wrong on our side.", "a profile bug: a protected slot has no placement"),
}


def outcome(refusal_reason: str, recovery_action: str | None = None) -> Outcome:
    return OUTCOMES.get((refusal_reason, recovery_action)) or OUTCOMES.get((refusal_reason, None)) or Outcome(
        "requires-manual-review", "Something went wrong on our side.", f"unmapped refusal {refusal_reason}: add it to outcomes.py")
