from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
import siblings  # noqa: E402

import bench_read  # noqa: E402


def test_by_model_sums_measures_over_jobs():
    summary = {"jobs": [
        {"model": "m", "repeat": 1, "measures": {"invariant": [3, 3], "answer": [1, 2]}},
        {"model": "m", "repeat": 2, "measures": {"invariant": [3, 3], "answer": [2, 2]}},
        {"model": "n", "repeat": 1, "measures": {"invariant": [2, 3]}},
    ]}
    table = bench_read.by_model(summary)
    assert table["m"]["invariant"] == [6, 6] and table["m"]["answer"] == [3, 4]
    assert table["n"]["invariant"] == [2, 3]
    assert bench_read.repeats(summary, "answer") == {"m": [0.5, 1.0]}


@pytest.mark.skipif(siblings.sibling("examples") is None or not (siblings.sibling("examples") / "gallery" / "results").exists(),
                    reason="the examples sibling with a graded gallery run is not checked out")
def test_committed_bench_run_holds_every_invariant():
    results = siblings.sibling("examples") / "gallery" / "results"
    summary = bench_read.load(bench_read.runs(results)[-1])
    table = bench_read.by_model(summary)
    assert all(row["invariant"][0] == row["invariant"][1] for row in table.values())


def test_the_vendored_domain2_run_reads_as_published():
    import domain2_read
    run_id, s2, size = domain2_read.load_vendored()
    assert (run_id, s2["status"], size) == ("20261012T052348Z-4a0ea5d", "pass", "recorded")
    at = {row["arm"]: row for row in s2["by_arm"] if str(row.get("tier")) == "8192"}
    assert round(at["truncate-pinned"]["aptitude"], 3) == 0.823
    assert round(at["cwa-state"]["paired"]["difference"], 3) == 0.147
    straddles = at["cwa-state-x"]["paired"]["interval"]
    assert straddles["low"] < 0 < straddles["high"], "model-written state is level with pinned truncation"
