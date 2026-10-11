"""Lab D: five items that are each wrong in exactly one way.

Each function returns one evidence.knowledge item for the help-center-search batch, built from the first chunk of the
corpus with `common.item(...)`, that the assembler will exclude with the code named in EXPECTED. Write the item that
earns exactly that code, and nothing else wrong with it. Give each item its own id (except reused_id, whose point
is the clash), so the five can be linted together with `uv run lint.py --impl labs --negatives`. `CWA_W2_IMPL=labs uv run pytest tests/test_lab_d.py` adds
each item to a valid snapshot and checks the trace.

The codes are in shared/contract/cwa/contract/reasons.json, in the order the assembler records them: an item that is
wrong in two ways gets the earlier code, so keep each item wrong in one way only.
"""

from __future__ import annotations

from common import Item

EXPECTED = {
    "claims_protected": ("tier_upgrade_not_allowed", "R-16"),
    "wrong_slot": ("producer_slot_not_allowed", "R-13"),
    "unmarked": ("untrusted_content_unmarked", "R-10"),
    "reused_id": ("duplicate_item_id", "R-2"),
    "no_relevance": ("missing_field:relevance", "R-13"),
}


def claims_protected() -> Item:
    """A chunk that declares itself protected."""
    raise NotImplementedError("Lab D")


def wrong_slot() -> Item:
    """A chunk addressed to governance.instructions."""
    raise NotImplementedError("Lab D")


def unmarked() -> Item:
    """A chunk that says injection_risk: none."""
    raise NotImplementedError("Lab D")


def reused_id() -> Item:
    """A chunk whose id another candidate already uses."""
    raise NotImplementedError("Lab D")


def no_relevance() -> Item:
    """A knowledge item with no rerank score."""
    raise NotImplementedError("Lab D")
