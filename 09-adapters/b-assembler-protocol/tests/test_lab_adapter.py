"""The adapter speaks the protocol. CWA_W9B_IMPL=labs runs these against yours."""

from __future__ import annotations

import base64
import json
import os

import pytest

import harness

WHICH = os.environ.get("CWA_W9B_IMPL", "solution")
COMMAND = harness.default_command(WHICH)
CASE = harness.CASES / "fixture-three-slot"


def test_assembled_exit_0_with_base64_payload_and_trace():
    out = harness.run_adapter(COMMAND, (CASE / "snapshot.json").read_bytes())
    assert out.kind == "assembled" and out.payload == (CASE / "expected.payload.txt").read_bytes()
    assert harness.comparable(out.trace) == harness.comparable(json.loads((CASE / "expected.trace.json").read_text()))


def test_refused_exit_0_with_null_payload():
    case = harness.CASES / "required-slot-missing"
    out = harness.run_adapter(COMMAND, (case / "snapshot.json").read_bytes())
    assert out.kind == "refused" and out.payload is None and out.trace["refused"]["bool"]


def test_rejected_exit_2_with_problems_on_stderr_and_nothing_on_stdout():
    rej = harness.REJECTIONS / "producer-in-two-batches"
    out = harness.run_adapter(COMMAND, (rej / "snapshot.json").read_bytes())
    assert out.kind == "rejected" and out.stderr and out.trace is None


def test_not_json_is_a_rejection():
    assert harness.run_adapter(COMMAND, b"\xff\xfe not json").kind == "rejected"


def test_unsupported_renderer_exit_3_with_the_exact_message():
    snapshot = json.loads((CASE / "snapshot.json").read_text())
    snapshot["renderer"] = "cwa-message-blocks/v9"
    out = harness.run_adapter(COMMAND, json.dumps(snapshot).encode())
    assert out.kind == "unsupported" and out.stderr == "renderer cwa-message-blocks/v9 is not provided"


def test_a_schema_break_is_rejected_even_when_a_component_is_also_missing():
    snapshot = json.loads((CASE / "snapshot.json").read_text())
    snapshot["renderer"] = "cwa-message-blocks/v9"
    del snapshot["budget"]
    assert harness.run_adapter(COMMAND, json.dumps(snapshot).encode()).kind == "rejected"
