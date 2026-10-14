"""The deployment gate and the refusal-to-outcome table."""

from __future__ import annotations

import json

import pytest
from cwa.registry import RegistryError, lock

import outcomes
import run

REFUSALS = ["required_slot_missing", "protected_slot_unplaced", "conflict_unresolved", "protected_content_over_budget", "slot_floor_over_budget", "evidence_required"]


def test_every_refusal_code_has_an_outcome():
    for code in REFUSALS:
        o = outcomes.outcome(code)
        assert o.action and o.user_message and o.operator_note
    assert outcomes.outcome("evidence_required", "request_context").action == "needs-info"
    assert outcomes.outcome("evidence_required", "retrieve_narrower").action == "precompute-and-retry"
    assert outcomes.outcome("protected_content_over_budget").action == "retry-larger-route"
    assert outcomes.outcome("something_new").action == "requires-manual-review"


def test_the_gate_refuses_without_a_lock_and_with_an_unevaluated_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "HERE", tmp_path)
    (tmp_path / "policy").mkdir()
    profile = json.loads((run.Path(__file__).resolve().parents[1] / "policy" / "profile.json").read_text())
    policy = json.loads((run.Path(__file__).resolve().parents[1] / "policy" / "route-policy.json").read_text())
    (tmp_path / "policy" / "profile.json").write_text(json.dumps(profile))
    (tmp_path / "policy" / "route-policy.json").write_text(json.dumps(policy))
    with pytest.raises(RegistryError, match="nothing has been promoted"):
        run.pinned("gpt-oss:20b")
    (tmp_path / "policy" / "registry.lock.json").write_text(json.dumps(lock([profile], [policy])))
    with pytest.raises(RegistryError, match="unevaluated"):
        run.pinned("gpt-oss:20b")
    profile["version"] += 1  # promotion names a model family: a new model target, a new version (R-20)
    profile["model_family"] = "gpt-oss:20b"
    profile["evaluation"] = {"status": "evaluated", "suite": "s", "date": "2026-10-01", "result": "5/5", "artifact": "a"}
    (tmp_path / "policy" / "profile.json").write_text(json.dumps(profile))
    (tmp_path / "policy" / "registry.lock.json").write_text(json.dumps(lock([profile], [policy])))
    assert run.pinned("gpt-oss:20b")["profile"]["id"] == profile["id"]
    with pytest.raises(RegistryError, match="not gpt-oss:120b"):
        run.pinned("gpt-oss:120b")
