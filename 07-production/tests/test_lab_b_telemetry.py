"""Lab B: span attributes carry decisions and digests, never content. CWA_W7_IMPL=labs checks yours."""

from __future__ import annotations

import impl
import telemetry


def test_attributes_identify_and_explain_the_assembly(status_record, which):
    attributes_for = impl.module("telemetry_attributes", which).attributes_for
    trace = status_record["inferences"][2]["trace"]
    attrs = attributes_for(trace)
    assert all(k.startswith("cwa.") for k in attrs)
    values = " ".join(str(v) for v in attrs.values())
    assert trace["context"]["snapshot_digest"] in values and trace["result"]["hash"] in values
    assert "obs:1: superseded" in values and "cap:delete_workspace: capability_not_allowed" in values
    assert trace["profile"]["id"] in values and trace["context"]["route_policy_version"] in values
    assert str(trace["result"]["input_tokens"]) in values


def test_attributes_carry_no_content(status_record, which):
    attributes_for = impl.module("telemetry_attributes", which).attributes_for
    for inference in status_record["inferences"]:
        values = " ".join(str(v) for v in attributes_for(inference["trace"]).values()).lower()
        bodies = [i["body"] for b in inference["snapshot"]["batches"] for i in b["items"]]
        for body in bodies:
            for sentence in [s.strip() for s in body.replace("\n", " ").split(".") if len(s.strip()) > 25]:
                assert sentence.lower() not in values, f"content leaked into a span: {sentence[:60]}"
        assert status_record["request"]["question"].lower() not in values


def test_attribute_values_are_otel_types(status_record, which):
    attributes_for = impl.module("telemetry_attributes", which).attributes_for
    for v in attributes_for(status_record["inferences"][0]["trace"]).values():
        assert isinstance(v, (str, int, float, bool)) or (isinstance(v, list) and all(isinstance(x, (str, int, float, bool)) for x in v))


def test_emit_makes_one_span_per_run_inference_and_call(status_record, which):
    calls = sum(len(i["steps"]) for i in status_record["inferences"])
    assert telemetry.emit("run_test", status_record, which) == 1 + len(status_record["inferences"]) + calls
