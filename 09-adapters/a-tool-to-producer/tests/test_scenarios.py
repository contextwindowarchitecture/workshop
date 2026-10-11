from __future__ import annotations

import json

import pytest
from cwa import Snapshot, assemble

import scenarios


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_scenario_is_what_the_code_builds_now(name):
    assert scenarios.stale(name) == [], "run `uv run scenarios.py --write`, then review the diff"


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_snapshot_replays_to_the_committed_request(name):
    d = scenarios.SCENARIOS / name
    result = assemble(Snapshot.from_json(json.loads((d / "snapshot.json").read_text(encoding="utf-8"))))
    payload = d / "payload.json"
    assert result.payload == (payload.read_bytes() if payload.exists() else None)
    assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == json.loads((d / "trace.json").read_text(encoding="utf-8"))


def _rows(name):
    return {r["item_id"]: r for r in json.loads((scenarios.SCENARIOS / name / "trace.json").read_text(encoding="utf-8"))["excluded"]}


def test_01_the_copy_outranks_the_original_and_the_route_keeps_the_copy():
    rows = _rows("01-retriever")
    assert rows["help:data-export@6#0"]["reason"] == "duplicate_content" and rows["help:data-export@6#0"]["duplicate_of"] == "help:exports-faq@2#0"
    assert rows["help:exports-faq@2#1"]["stage"] == "producer"


def test_02_and_03_differ_only_in_what_the_trace_can_see():
    loud, silent = _rows("02-memory-reported"), _rows("03-memory-silent-fault")
    assert loud["mem:u_ada:0003"]["reason"] == "revoked" and loud["mem:u_ada:0001"]["reason"] == "expired"
    assert "mem:u_ada:0003" not in silent and "mem:u_ada:0001" not in silent


def test_04_the_older_status_poll_is_superseded():
    rows = _rows("04-observations-superseded")
    assert rows["obs:2"]["reason"] == "superseded" and rows["obs:2"]["superseded_by"] == "obs:3"


def test_05_tool_specs_from_the_adapter_are_excluded():
    rows = _rows("05-specs-as-items-fault")
    assert {rows[f"mcp-cap:{n}"]["reason"] for n in ("get_account", "list_members", "get_service_status")} == {"producer_slot_not_allowed"}


def test_06_a_member_is_not_offered_list_members():
    rows = _rows("06-member-not-granted")
    assert rows["cap:list_members"]["reason"] == "capability_not_allowed" and rows["cap:list_members"]["stage"] == "producer"
