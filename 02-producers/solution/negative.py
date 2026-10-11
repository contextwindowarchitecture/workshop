"""Lab D, solved: five items that are each wrong in exactly one way, and the code each earns at admission."""

from __future__ import annotations

from common import Item, chunks, item

# (function name, the code the assembler records, the requirement)
EXPECTED = {
    "claims_protected": ("tier_upgrade_not_allowed", "R-16"),
    "wrong_slot": ("producer_slot_not_allowed", "R-13"),
    "unmarked": ("untrusted_content_unmarked", "R-10"),
    "reused_id": ("duplicate_item_id", "R-2"),
    "no_relevance": ("missing_field:relevance", "R-13"),
}


def _chunk_item(tag: str, **overrides) -> Item:
    chunk = chunks()[0]
    fields = dict(id=f"{chunk.id}:neg-{tag}", slot="evidence.knowledge", source=f"help-center:{chunk.article}",
                  source_version=chunk.version, authority="reference_only", trust="verified", freshness=chunk.updated,
                  relevance=9.0, lineage="verbatim", injection_risk="untrusted_content", body=chunk.text)
    fields.update(overrides)
    return item(**fields)


def claims_protected() -> Item:
    """A chunk that declares itself protected. Only the route's versioned policy raises a slot's tier."""
    return _chunk_item("protected", tier="protected")


def wrong_slot() -> Item:
    """A chunk addressed to governance.instructions. A retrieval producer's kind bounds its slots, whatever the route lists."""
    return _chunk_item("slot", slot="governance.instructions", authority="governing", injection_risk="none")


def unmarked() -> Item:
    """A chunk that says injection_risk: none. Retrieved text is always marked, as given or as filled."""
    return _chunk_item("unmarked", injection_risk="none")


def reused_id() -> Item:
    """A chunk whose id is one another candidate already uses. Ids are unique across the snapshot."""
    return _chunk_item("reused", id=chunks()[0].id)


def no_relevance() -> Item:
    """A knowledge item with no rerank score. Every evidence.knowledge item carries relevance."""
    bad = _chunk_item("no-relevance")
    del bad["relevance"]
    return bad
