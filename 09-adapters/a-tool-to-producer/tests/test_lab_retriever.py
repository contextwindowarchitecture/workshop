"""Lab 1: LlamaIndex hits to a retrieval batch."""

from __future__ import annotations

import pytest

import impl
from tests.conftest import assembled, codes, solution_batches


@pytest.fixture
def adapt(which):
    return impl.module("retriever_adapter", which).adapt


def test_one_item_per_hit_with_provenance_from_metadata(ada, hits, adapt):
    b = adapt(hits, ada)
    assert b["producer"] == {"id": "help-center-search", "kind": "retrieval"}
    by_id = {i["id"]: i for i in b["items"]}
    assert set(by_id) | {r["item_id"] for r in b["excluded"]} == {h.node.node_id for h in hits}
    for h in hits:
        i = by_id.get(h.node.node_id)
        if i is None:
            continue
        assert i["source"] == f"help-center:{h.node.metadata['article']}"
        assert i["source_version"] == str(h.node.metadata["version"]) and i["freshness"] == h.node.metadata["updated"]
        assert i["relevance"] == round(float(h.score), 3) and i["body"] == h.node.get_content()
        assert i["slot"] == "evidence.knowledge" and i["authority"] == "reference_only"
        assert i["injection_risk"] == "untrusted_content" and i["lineage"] == "verbatim"


def test_near_duplicates_reported_exact_copies_kept(ada, hits, adapt):
    b = adapt(hits, ada)
    reported = [r for r in b["excluded"] if r["reason"] == "duplicate_content"]
    assert reported and all(r["stage"] == "producer" for r in reported)
    kept = {i["id"] for i in b["items"]}
    assert all(r["duplicate_of"] in kept for r in reported)
    bodies = [i["body"] for i in b["items"]]
    assert len(bodies) != len(set(bodies)), "the word-for-word copy stays for the route's dedupe: exact"


def test_admitted_and_the_route_dedupes_the_copy(ada, hits, adapt):
    batches, grant = solution_batches(ada)
    batches = [b for b in batches if b["producer"]["id"] != "help-center-search"] + [adapt(hits, ada)]
    _, result = assembled(ada, batches, grant)
    assert not result.refused
    assembler = codes(result.trace, "assembler")
    assert "duplicate_content" in assembler.values()
    assert set(assembler.values()) <= {"duplicate_content", "below_threshold", "source_diversity_cap"}
    assert any(r["slot"] == "evidence.knowledge" for r in result.trace["included"])
