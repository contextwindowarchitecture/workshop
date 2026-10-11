from __future__ import annotations

import json

import pytest

import scenarios
from solution import context


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_scenario_is_what_the_code_builds_now(name):
    assert scenarios.stale(name) == [], "run `uv run scenarios.py --write`, then review the diff"


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_snapshot_replays_to_the_committed_request(name):
    d = scenarios.SCENARIOS / name
    result = context.assemble(json.loads((d / "snapshot.json").read_text(encoding="utf-8")))
    payload = d / "payload.json"
    assert result.payload == (payload.read_bytes() if payload.exists() else None)
    assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == json.loads((d / "trace.json").read_text(encoding="utf-8"))


def test_there_are_five_scenarios():
    assert scenarios.names() == ["01-ada-export", "02-ben-plan-conflict", "03-off-topic", "04-long-conversation", "05-memory-leak"]
