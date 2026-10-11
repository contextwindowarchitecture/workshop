from __future__ import annotations

import json
from pathlib import Path

import generate
import verify
from cwa import Snapshot, assemble
from jsonschema import Draft202012Validator

CONTRACT = generate.CONTRACT
CASE = generate.CASE


def _schema(name):
    return Draft202012Validator(json.loads((CONTRACT / "schema" / name).read_text(encoding="utf-8")))


def test_committed_case_is_what_the_table_implies():
    for name, content in generate.files().items():
        assert (CASE / name).read_bytes() == content, f"{name} is stale: run uv run generate.py"


def test_a_refusal_commits_no_payload():
    assert not (CASE / "expected.payload.txt").exists()
    expected = json.loads((CASE / "expected.trace.json").read_text(encoding="utf-8"))
    assert expected["result"] is None and expected["included"] == [] and expected["refused"] == {"bool": True, "reason": "conflict_unresolved"}


def test_snapshot_and_trace_are_valid_against_the_published_schemas():
    snapshot = json.loads((CASE / "snapshot.json").read_text(encoding="utf-8"))
    expected = json.loads((CASE / "expected.trace.json").read_text(encoding="utf-8"))
    assert list(_schema("snapshot.schema.json").iter_errors(snapshot)) == []
    assert list(_schema("trace.schema.json").iter_errors(expected)) == []


def test_reference_assembler_passes_the_case():
    document = json.loads((CASE / "snapshot.json").read_text(encoding="utf-8"))
    expected = json.loads((CASE / "expected.trace.json").read_text(encoding="utf-8"))
    result = assemble(Snapshot.from_json(document))
    assert result.payload is None
    assert verify.first_difference(verify.comparable(result.trace), verify.comparable(expected)) is None


def test_the_case_catches_the_uncovered_defect():
    document = json.loads((CASE / "snapshot.json").read_text(encoding="utf-8"))
    expected = json.loads((CASE / "expected.trace.json").read_text(encoding="utf-8"))
    broken = verify.run(verify.broken_assembler(), document)
    assert broken.payload is not None, "the defect applies the tie-break and assembles"
    assert verify.first_difference(verify.comparable(broken.trace), verify.comparable(expected)) == "/conflicts/0/decided_by"


def test_the_published_corpus_does_not_catch_it_where_this_case_does():
    """conflict-fact's f-tie group has two leaders at the same instant, so the clock cannot break it even without permission."""
    corpus = json.loads((CONTRACT / "conformance" / "cases" / "conflict-fact" / "snapshot.json").read_text(encoding="utf-8"))
    tie = next(g for g in corpus["conflicts"] if g["id"] == "f-tie")
    freshness = {i["id"]: i["freshness"] for b in corpus["batches"] for i in b["items"] if i["id"] in tie["items"]}
    assert len(set(freshness.values())) == 1
    assert "freshness_tiebreak" not in corpus["route_policy"]["facts"][tie["fact"]]
