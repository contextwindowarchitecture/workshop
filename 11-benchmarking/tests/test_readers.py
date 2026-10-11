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


@pytest.mark.skipif(siblings.sibling("examples") is None or not (siblings.sibling("examples") / "bench" / "results").exists(),
                    reason="the examples sibling with a graded bench run is not checked out")
def test_committed_bench_run_holds_every_invariant():
    results = siblings.sibling("examples") / "bench" / "results"
    summary = bench_read.load(bench_read.runs(results)[-1])
    table = bench_read.by_model(summary)
    assert all(row["invariant"][0] == row["invariant"][1] for row in table.values())
