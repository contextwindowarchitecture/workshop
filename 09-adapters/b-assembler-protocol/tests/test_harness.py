"""The harness judges by the published pass rule and reports in the published shape."""

from __future__ import annotations

import json

from jsonschema import Draft202012Validator

import harness
import scenarios


def test_first_difference_points_at_the_first_divergence_in_utf16_key_order():
    assert harness.first_difference({"a": 1, "b": [1, 2]}, {"a": 1, "b": [1, 3]}) == "/b/1"
    assert harness.first_difference({"b": 1}, {"a": 1, "b": 1}) == "/a"
    assert harness.first_difference({"x": {"y": 1}}, {"x": {"y": 1}}) is None


def test_a_changed_expectation_fails_with_a_pointer():
    case = harness.CASES / "fixture-three-slot"
    out = harness.run_adapter(harness.default_command("solution"), (case / "snapshot.json").read_bytes())
    expected = json.loads((case / "expected.trace.json").read_text())
    expected["included"][0]["tokens"] += 1
    where = harness.first_difference(harness.comparable(out.trace), harness.comparable(expected))
    assert where == "/included/0/tokens"


def test_the_committed_report_is_current_and_valid():
    report = json.loads(scenarios.REPORT.read_text(encoding="utf-8"))
    schema = json.loads((harness.CONTRACT / "schema" / "conformance_report.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(report)
    assert all(c["outcome"] == "passed" for c in report["cases"]) and len(report["cases"]) == 65
    assert all(r["outcome"] == "rejected" for r in report["rejections"]) and len(report["rejections"]) == 25
    assert scenarios.stale("conformance-report") == []
