"""The committed scenarios are what the solution builds now, and each one shows what it is there to show."""

from __future__ import annotations

import json

import pytest
from cwa import Snapshot, assemble

import scenarios
from solution import negative


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_scenario_is_what_the_code_builds_now(name):
    assert scenarios.stale(name) == [], "run `uv run scenarios.py --write`, then review the diff"


@pytest.mark.parametrize("name", scenarios.names())
def test_the_committed_snapshot_replays_to_the_committed_request(name):
    directory = scenarios.SCENARIOS / name
    result = assemble(Snapshot.from_json(json.loads((directory / "snapshot.json").read_text(encoding="utf-8"))))
    payload = directory / "payload.json"
    assert result.payload == (payload.read_bytes() if payload.exists() else None)
    trace = json.loads((directory / "trace.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == trace


def _trace(name):
    return json.loads((scenarios.SCENARIOS / name / "trace.json").read_text(encoding="utf-8"))


def _codes(name):
    return {r["item_id"]: r["reason"] for r in _trace(name)["excluded"]}


def test_01_shows_producer_and_assembler_dedupe_side_by_side():
    rows = {r["item_id"]: r for r in _trace("01-ada-export")["excluded"]}
    stages = {r["stage"] for r in rows.values() if r["reason"] == "duplicate_content"}
    assert stages == {"producer", "assembler"}
    assert _codes("01-ada-export")["mem:u_ada:0003"] == "revoked"


def test_02_reports_expired_memories_from_the_producer():
    c = _codes("02-cho-refund")
    assert c["mem:u_cho:0002"] == "expired" and c["mem:u_cho:0003"] == "expired"


def test_03_scope_keeps_another_users_memory_out():
    assert _codes("03-memory-leak")["mem:u_ada:0005"] == "out_of_scope"


def test_04_a_stale_account_read_is_excluded():
    assert _codes("04-stale-account-read")["account:w_kitewood:plan"] == "stale_state"


def test_05_variants_are_used_before_anything_is_omitted():
    t = _trace("05-budget-variants")
    assert t["compressed"], "the precomputed lead sentences should be swapped in"
    assert all(r["slot"] == "evidence.knowledge" for r in t["compressed"])


@pytest.mark.parametrize("name", list(negative.EXPECTED))
def test_each_negative_scenario_records_its_code(name):
    expected, _ = negative.EXPECTED[name]
    bad_id = getattr(negative, name)()["id"]
    assert _codes(f"neg-{name.replace('_', '-')}")[bad_id] == expected
