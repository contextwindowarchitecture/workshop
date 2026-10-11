"""Lab A: the review list. CWA_W4_IMPL=labs checks yours against the answer; the default checks the solution's."""

from __future__ import annotations

import json

import impl
from app import producers
from request import corpus

UNFAITHFUL = {"help:data-export@6#2", "help:plans@9#3", "help:refunds@4#1", "help:roles@4#1"}


def test_the_unfaithful_summaries_are_rejected_with_a_reason(which):
    review = json.loads(impl.path("reviewed.json", which).read_text(encoding="utf-8"))
    approved, rejected = set(review["approved"]), review.get("rejected", {})
    assert UNFAITHFUL.isdisjoint(approved), f"still approved: {sorted(UNFAITHFUL & approved)}"
    assert UNFAITHFUL <= set(rejected), f"rejected without a reason: {sorted(UNFAITHFUL - set(rejected))}"
    assert all(rejected[i].strip() for i in UNFAITHFUL)


def test_every_faithful_summary_is_still_approved(which):
    review = json.loads(impl.path("reviewed.json", which).read_text(encoding="utf-8"))
    faithful = {c.id for c in corpus.chunks()} - UNFAITHFUL
    assert faithful <= set(review["approved"]), f"faithful but not approved: {sorted(faithful - set(review['approved']))}"


def test_only_approved_summaries_become_variants(which):
    by_id = {c.id: c for c in corpus.chunks()}
    for bad in UNFAITHFUL:
        assert producers.variants_for(by_id[bad], which) == []
    v = producers.variants_for(by_id["help:billing@5#0"], which)
    assert len(v) == 1 and v[0]["lineage"] == "summarised" and v[0]["id"] == "help:billing@5#0~summary"
    assert len(v[0]["body"]) < len(by_id["help:billing@5#0"].text)


def test_the_exact_copy_shares_the_summary_by_content_hash(which):
    by_id = {c.id: c for c in corpus.chunks()}
    a, b = producers.variants_for(by_id["help:data-export@6#0"], which), producers.variants_for(by_id["help:exports-faq@2#0"], which)
    assert a and b and a[0]["body"] == b[0]["body"] and a[0]["id"] != b[0]["id"]
