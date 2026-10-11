"""What the committed scenarios show about fitting, recovery and the review."""

from __future__ import annotations

import json

import scenarios
from tests.conftest import trace


def test_01_fits_on_the_small_route_without_compression():
    t = trace("01-export", "1-account-help-small")
    assert not t["refused"]["bool"] and t["compressed"] == []


def test_02_variants_are_used_before_evidence_is_omitted():
    t = trace("02-export-squeezed", "1-account-help-small")
    assert not t["refused"]["bool"]
    compressed = {r["item_id"] for r in t["compressed"]}
    assert compressed, "summaries should be swapped in under pressure"
    omitted = {r["item_id"] for r in t["excluded"] if r["reason"] == "over_budget"}
    assert any(i.startswith("turn:") for i in omitted), "history goes first in the fitting order"
    for r in t["compressed"]:
        assert r["variant_id"].endswith("~summary") and r["to"] < r["from"]


def test_03_protected_content_refuses_before_any_reduction_then_escalates():
    small = trace("03-pasted-log", "1-account-help-small")
    assert small["refused"] == {"bool": True, "reason": "protected_content_over_budget"}
    assert small["included"] == [] and small["compressed"] == [] and small["result"] is None
    large = trace("03-pasted-log", "2-account-help")
    assert not large["refused"]["bool"] and large["result"]["input_tokens"] > 2000


def test_04_recovery_action_depends_on_whether_omitted_evidence_had_variants():
    t = trace("04-recovery", "1-account-help-small")
    assert t["refused"]["reason"] == "evidence_required"
    assert t["recovery"]["action"] == "precompute_summary", "an omitted evidence item had no variant: its summary was rejected in review"


def test_05_an_unreviewed_summary_reaches_the_payload():
    t = trace("05-unreviewed", "1-account-help-small")
    rejected = set(json.loads((scenarios.SCENARIOS.parent / "solution" / "reviewed.json").read_text(encoding="utf-8"))["rejected"])
    swapped = {r["item_id"] for r in t["compressed"]}
    assert swapped & rejected, "with everything approved, an unfaithful summary is what the model reads"
    payload = (scenarios.SCENARIOS / "05-unreviewed" / "1-account-help-small.payload.json").read_bytes()
    assert b"billed monthly or $23 annually" in payload or b"can change billing" in payload
