from __future__ import annotations

import json

import pytest
from cwa import Snapshot, assemble

import scenarios


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_scenario_is_what_the_code_builds_now(name):
    assert scenarios.stale(name) == [], "run `uv run scenarios.py --write`, then review the diff"


@pytest.mark.parametrize("name", scenarios.names())
def test_every_committed_snapshot_replays_to_its_committed_trace(name):
    d = scenarios.SCENARIOS / name
    for snap in sorted(d.glob("*.snapshot.json")):
        stem = snap.name[: -len(".snapshot.json")]
        result = assemble(Snapshot.from_json(json.loads(snap.read_text(encoding="utf-8"))))
        payload = d / f"{stem}.payload.json"
        assert result.payload == (payload.read_bytes() if payload.exists() else None)
        assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == json.loads((d / f"{stem}.trace.json").read_text(encoding="utf-8"))
