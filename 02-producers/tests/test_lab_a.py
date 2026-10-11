"""Lab A: the retrieval producer."""

from __future__ import annotations

import pytest

import common
import impl
from tests.conftest import assembled, codes


@pytest.fixture
def search(which):
    return impl.module("retrieval", which).help_center_search


def test_one_scored_item_per_chunk_and_never_a_blob(ada, search):
    b = search(ada)
    assert b["producer"] == {"id": "help-center-search", "kind": "retrieval"}
    assert len(b["items"]) >= 4
    for i in b["items"]:
        assert i["slot"] == "evidence.knowledge" and i["authority"] == "reference_only"
        assert isinstance(i["relevance"], (int, float))
        assert i["injection_risk"] == "untrusted_content" and i["lineage"] == "verbatim"
        assert i["source"].startswith("help-center:") and i["source_version"]
        assert "\n\n" not in i["body"], "a body with two paragraphs is a merged blob"


def test_near_duplicates_are_dropped_and_reported(ada, search):
    b = search(ada)
    reported = [r for r in b["excluded"] if r["reason"] == "duplicate_content"]
    assert reported, "the exports FAQ's reworded paragraph should be reported as a near-duplicate"
    kept = {i["id"] for i in b["items"]}
    for r in reported:
        assert r["stage"] == "producer" and r["duplicate_of"] in kept and r["item_id"] not in kept


def test_exact_copies_are_left_for_the_assembler(ada, search):
    bodies = [i["body"] for i in search(ada)["items"]]
    assert len(bodies) != len(set(bodies)), "the exact copy in exports-faq stays in the batch for dedupe: exact"


def test_variants_are_precomputed_and_well_formed(ada, search):
    with_variants = [i for i in search(ada)["items"] if i["variants"]]
    assert with_variants
    for i in with_variants:
        ids = [v["id"] for v in i["variants"]]
        assert len(set(ids)) == len(ids) and i["id"] not in ids
        for v in i["variants"]:
            assert v["lineage"] == "extracted" and v["method"] and len(v["body"]) < len(i["body"])


def test_the_assembler_admits_them_and_dedupes_the_exact_copy(ada, search, baseline):
    batches = [b for b in baseline if b["producer"]["id"] != "help-center-search"] + [search(ada)]
    _, result = assembled(ada, batches)
    assert not result.refused
    reasons = set(codes(result.trace, "assembler").values())
    assert reasons <= {"duplicate_content", "below_threshold", "source_diversity_cap", "over_budget"}, reasons
    assert "duplicate_content" in reasons, "the exact copy should be excluded by the route's dedupe: exact"
    assert any(r["slot"] == "evidence.knowledge" for r in result.trace["included"])
