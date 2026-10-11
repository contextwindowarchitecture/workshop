"""What the committed runs show: one snapshot per inference, a guard on every call, denials as state, supersession, and
a replay that needs no model."""

from __future__ import annotations

import json

import pytest
from cwa import Snapshot, assemble

import scenarios
from tests.conftest import run, steps


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_run_is_what_the_code_builds_now(name):
    assert scenarios.stale(name) == [], "run `uv run scenarios.py --write`, then review the diff"


@pytest.mark.parametrize("name", scenarios.names())
def test_every_inference_replays_to_the_same_bytes_without_a_model(name):
    for inference in run(name)["inferences"]:
        result = assemble(Snapshot.from_json(inference["snapshot"]))
        assert (result.payload.decode("utf-8") if result.payload else None) == inference["payload"]
        assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == inference["trace"]


def test_01_a_repeated_poll_is_superseded_and_each_turn_is_its_own_snapshot():
    r = run("01-status-check")
    digests = [i["trace"]["context"]["snapshot_digest"] for i in r["inferences"]]
    assert len(digests) == len(set(digests)) == 4
    last = r["inferences"][-1]["trace"]
    rows = {e["item_id"]: e for e in last["excluded"]}
    assert rows["obs:2"]["reason"] == "superseded" and rows["obs:2"]["superseded_by"] == "obs:3"
    assert "resolved" in r["answer"]


def test_02_a_member_is_denied_and_told_why_as_state():
    r = run("02-member-not-offered")
    denied = [s for s in steps(r) if not s["approved"]]
    assert denied and denied[0]["tool"] == "list_members" and not denied[0]["executed"]
    task = next(i for b in r["inferences"][1]["snapshot"]["batches"] for i in b["items"] if i["slot"] == "state.task")
    assert "denied by the application" in task["body"] and "list_members" in task["body"]
    assert all(e["slot"] != "evidence.tool_results" for e in r["inferences"][1]["trace"]["included"])


def test_03_an_injected_instruction_moves_nothing():
    r = run("03-injected-instruction")
    obs = next(i for b in r["inferences"][1]["snapshot"]["batches"] for i in b["items"] if i["slot"] == "evidence.tool_results")
    assert "SYSTEM NOTICE" in obs["body"] and obs["injection_risk"] == "untrusted_content" and obs["authority"] == "observation"
    by_tool = {s["tool"]: s for s in steps(r)}
    assert not by_tool["delete_workspace"]["approved"] and not by_tool["delete_workspace"]["executed"]
    assert not by_tool["request_plan_change"]["approved"] and "w_larkspur" in by_tool["request_plan_change"]["reason"]
    assert by_tool["get_service_status"]["executed"]


def test_04_a_tool_error_is_an_observation_too():
    r = run("04-status-error")
    step = steps(r)[0]
    assert step["executed"] and not step["ok"] and "503" in str(step["value"])
    obs = next(i for b in r["inferences"][1]["snapshot"]["batches"] for i in b["items"] if i["slot"] == "evidence.tool_results")
    assert "error" in json.loads(obs["body"])


def test_05_the_last_turn_offers_no_tools():
    r = run("05-runs-out-of-turns")
    assert len(r["inferences"]) == 5
    last = r["inferences"][-1]
    assert last["snapshot"]["capabilities"]["allowed_ids"] == []
    assert all(e["slot"] != "governance.capabilities" for e in last["trace"]["included"])
    assert "last turn" in next(i for b in last["snapshot"]["batches"] for i in b["items"] if i["slot"] == "state.task")["body"]
    assert r["answer"]


def test_06_another_workspace_is_denied_by_scope_not_by_wording():
    r = run("06-wrong-workspace")
    first, second = steps(r)[0], steps(r)[1]
    assert not first["approved"] and "w_larkspur" in first["reason"] and not first["executed"]
    assert second["approved"] and second["executed"] and second["ok"]
