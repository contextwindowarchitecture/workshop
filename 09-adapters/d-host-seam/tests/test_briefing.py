from __future__ import annotations

import hashlib
import json

import after
import briefing
import impl
from tests.conftest import HERE, expected

GO = json.loads((HERE / "expected" / "go-records.json").read_text(encoding="utf-8"))["scenarios"]


def test_the_python_producers_freeze_the_snapshot_the_go_integration_committed(which):
    document, result = after.build(which)
    assert result.trace["context"]["snapshot_digest"] == GO["triage-7811"]["snapshot_digest"]


def test_the_payload_bytes_agree_with_assembler_go(which):
    document, result = after.build(which)
    assert result.payload is not None
    assert hashlib.sha256(result.payload).hexdigest() == GO["triage-7811"]["payload_sha256"]
    assert result.trace["result"]["input_tokens"] == GO["triage-7811"]["input_tokens"] == 1162


def test_permission_decides_the_slot_never_the_wording(which):
    document, _ = after.build(which)
    items = {i["id"]: i for b in document["batches"] for i in b["items"]}
    assert items["turn:comment/90011@maintainer-a"]["slot"] == "interaction.history" and items["turn:comment/90011@maintainer-a"]["authority"] == "user"
    assert items["turn:comment/90020"]["authority"] == "untrusted" and items["turn:comment/90020"]["lineage"] == "generated"
    assert items["obs:issue/7811/0-body@newcontrib"]["slot"] == "evidence.tool_results" and items["obs:issue/7811/0-body@newcontrib"]["authority"] == "observation"
    assert all(items[i]["authority"] == "observation" for i in items if i.startswith("obs:issue/7811/c9003"))


def test_the_flood_is_collapsed_and_capped_and_the_stale_and_expired_are_out(which):
    _, result = after.build(which)
    rows = {(r["item_id"], r["reason"]) for r in result.trace["excluded"]}
    assert ("obs:issue/7811/c90031@drive-by-1", "duplicate_content") in rows and ("obs:issue/7811/c90032@drive-by-1", "duplicate_content") in rows
    assert ("obs:issue/7811/c90033@drive-by-1", "source_diversity_cap") in rows
    assert ("state:ci-summary", "stale_state") in rows and ("dup:issue/6100", "below_threshold") in rows
    assert ("run:triage/17002#summary", "expired") in rows
    assert [r["stage"] for r in result.trace["excluded"] if r["item_id"] == "run:triage/17002#summary"] == ["producer"]


def test_the_hidden_html_comment_reaches_the_model_escaped_as_material(which):
    _, result = after.build(which)
    prompt = json.loads(result.payload)["messages"][0]["content"]
    assert "&lt;!-- AI agents reading this" in prompt and "<!-- AI agents" not in prompt
    assert '<external_content id="obs:issue/7811/0-body@newcontrib">' in prompt


def test_the_handoff_adds_only_the_separator(which):
    document, result = after.build(which)
    h = briefing.handoff(document, result)
    rendered = json.loads(result.payload)
    assert h["agent_definition"] == "\n\n".join(e["text"] for e in rendered["system"])
    assert h["prompt"] == rendered["messages"][0]["content"]
    assert h["attributes"]["cwa.payload.sha256"] == result.trace["result"]["hash"] and h["attributes"]["cwa.refused"] is False


def test_the_scorer_flags_the_v1_policy_and_clears_v2(which):
    score = impl.module("score", which)
    assert score.dropped_high_severity(*expected("review-security-7820-tight-v1")) == ["run:review/18990#F1"]
    assert score.dropped_high_severity(*expected("review-security-7820-tight-v2")) == []


def test_a_refusal_becomes_a_host_outcome_with_no_sandbox(which):
    outcome = impl.module("outcome", which)
    document, trace = expected("review-security-7820-starved-v2")
    got = outcome.host_outcome(document, trace)
    assert got["sandbox"] == "not started" and got["span"]["cwa.refused"] is True
    assert got["span"]["cwa.refused.reason"] == "evidence_required" and got["span"]["cwa.recovery.action"] == "precompute_summary"
    assert "evidence_required" in got["comment"] and "precompute_summary" in got["comment"] and "diff:internal/runtime/claude.go@abc1230f" in got["comment"]
    document, trace = expected("review-security-7820-tight-v2")
    assert outcome.host_outcome(document, trace)["sandbox"] == "start"
