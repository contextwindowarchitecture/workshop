"""Every run as OpenTelemetry spans: one per run, one per inference, one per tool call, built from the run record.

The spans carry what CWA decided, never what users wrote: profile, route policy version, snapshot digest, payload hash,
token count, the ids sent, compressed and excluded with their reasons, the conflict groups, and the guard's verdict on
each call. The snapshot digest links to the store, which holds the content under its own access rules.

    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318   # any OTLP/HTTP backend: Jaeger, Tempo, Honeycomb, Langfuse
    CWA_W7_TRACE_CONSOLE=1                              # print each span as JSON

With neither set, spans are created and dropped. Lab B is attributes_for() in labs/telemetry_attributes.py.
"""

from __future__ import annotations

import os
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

import impl

TRACER = trace.get_tracer("cwa-workshop.w7")
_configured = False


def configure() -> None:
    global _configured
    if _configured:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": "fernway-account-agent"}))
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    if os.environ.get("CWA_W7_TRACE_CONSOLE"):
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _configured = True


def emit(run_id: str, record: dict[str, Any], which: str | None = None) -> int:
    """One span per run, inference and tool call, with the attributes the chosen attributes_for() returns."""
    configure()
    attributes_for = impl.module("telemetry_attributes", which).attributes_for
    count = 0
    with TRACER.start_as_current_span("agent.run", attributes={"cwa.run_id": run_id, "cwa.user": record["request"]["user"],
                                                              "cwa.model": record["model"], "cwa.answered": record["answer"] is not None}):
        count += 1
        for inference in record["inferences"]:
            with TRACER.start_as_current_span("cwa.assemble", attributes=attributes_for(inference["trace"])):
                count += 1
                for step in inference["steps"]:
                    with TRACER.start_as_current_span(f"tool {step['tool']}", attributes={
                            "cwa.tool": step["tool"], "cwa.guard.approved": step["approved"], "cwa.guard.reason": step["reason"],
                            "cwa.tool.executed": step["executed"], "cwa.tool.ok": step["ok"]}):
                        count += 1
    return count
