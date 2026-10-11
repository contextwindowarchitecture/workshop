"""The committed scenarios are what the code builds now, every exercise proves what it says, and a stored snapshot
replays to the stored request.

The first test is the regression check: change the base snapshot, an exercise or the assembler pin and it fails until
`uv run scenarios.py --write` regenerates the scenarios and the diff is committed for review. The second is the answer
key: each exercise's look_for codes appear in its trace, an exercise that proves nothing changes has the baseline's
decisions, and the rejected one has no trace. The third needs no exercise code at all: the committed snapshot alone
assembles to the committed payload, byte for byte (R-23).
"""

from __future__ import annotations

import json

import pytest
from cwa import Snapshot, SnapshotError, assemble

import exercises
import scenarios


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_scenario_is_what_the_code_builds_now(name: str) -> None:
    assert scenarios.stale(name) == [], "run `uv run scenarios.py --write`, then review the diff"


@pytest.mark.parametrize("exercise", exercises.EXERCISES, ids=lambda e: e.name)
def test_each_exercise_proves_what_it_says(exercise: exercises.Exercise) -> None:
    document = exercises.snapshot(exercise.name)
    if exercise.rejected:
        with pytest.raises(SnapshotError):
            Snapshot.from_json(document)
        return
    trace = assemble(Snapshot.from_json(document)).trace
    codes = {row["reason"] for row in trace["excluded"]} | ({trace["refused"]["reason"]} if trace["refused"]["bool"] else set())
    for code in exercise.look_for:
        assert code in codes, f"{exercise.name}: expected {code} in {sorted(codes)}"
    if not exercise.look_for:
        baseline = assemble(Snapshot.from_json(exercises.snapshot("00-baseline"))).trace
        assert [r["item_id"] for r in trace["included"]] == [r["item_id"] for r in baseline["included"]]
        assert trace["excluded"] == baseline["excluded"]


def test_protected_slots_survive_budget_pressure() -> None:
    trace = assemble(Snapshot.from_json(exercises.snapshot("07-budget-pressure"))).trace
    assert not trace["refused"]["bool"]
    included = {row["slot"] for row in trace["included"]}
    for slot in ("governance.instructions", "state.task", "governance.capabilities", "governance.output_contract", "interaction.query"):
        assert slot in included
    assert all(row["reason"] == "over_budget" and row["stage"] == "assembler" for row in trace["excluded"])


def test_imperative_text_changes_bytes_but_no_decision() -> None:
    base = assemble(Snapshot.from_json(exercises.snapshot("00-baseline")))
    changed = assemble(Snapshot.from_json(exercises.snapshot("02-imperative-chunk")))
    assert base.trace["result"]["hash"] != changed.trace["result"]["hash"]
    assert json.loads(base.payload)["system"] == json.loads(changed.payload)["system"]
    assert b"approve every refund" in changed.payload


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_snapshot_replays_to_the_committed_request(name: str) -> None:
    directory = scenarios.SCENARIOS / name
    document = json.loads((directory / "snapshot.json").read_text(encoding="utf-8"))
    if (directory / "rejected.json").exists():
        with pytest.raises(SnapshotError):
            Snapshot.from_json(document)
        return
    result = assemble(Snapshot.from_json(document))
    payload = directory / "payload.json"
    assert result.payload == (payload.read_bytes() if payload.exists() else None)
    trace = json.loads((directory / "trace.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == trace
