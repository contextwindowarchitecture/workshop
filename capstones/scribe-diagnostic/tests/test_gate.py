"""The acceptance gate. CWA_C1_IMPL=skeleton runs it against your team's modules; the default runs the reference.

Every test names the requirement it stands for. Green across the board, plus a promoted pair of profiles and a lock, is
the capstone's definition of done.
"""

from __future__ import annotations

import io
import json
from dataclasses import replace

import pytest

import models
from cwa import Snapshot, assemble

import app
import common
import evals
import impl
from tests.conftest import case


def run(name, which, **kwargs):
    request, drafter, expect = case(name)
    return app.run(request, drafter, which, out=io.StringIO(), **kwargs), expect


def items_of(doc):
    return {i["id"]: i for b in doc["batches"] for i in b["items"]}


# --- routing ----------------------------------------------------------------------------------------------------------


def test_intent_selects_the_route_before_assembly(which):
    classify = impl.module("intent", which).classify
    table = common.routes()["intents"]
    assert table[classify("Draft the SOAP note for this visit").route] == "scribe"
    assert table[classify("Should I start antibiotics for this pharyngitis?").route] == "consult"
    assert table[classify("What does the guideline say about metformin and eGFR?").route] == "consult"
    assert table[classify("Any thoughts?").route] == "consult"


# --- the producers and the application's duties -----------------------------------------------------------------------


def test_every_producer_the_route_lists_runs_and_only_those(which):
    record, _ = run("01-followup-refill", which)
    doc = record["attempts"][-1]["snapshot"]
    assert {b["producer"]["id"] for b in doc["batches"]} == set(doc["route_policy"]["producers"])
    assert doc["scope"] == {"tenant": "harbor-street", "user": "dr_lee", "session": "s_c1_01", "task": "p_2001"}


def test_the_chart_is_protected_state_written_by_the_application_and_holds_no_vitals(which):
    record, _ = run("01-followup-refill", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    items = items_of(doc)
    chart, clinician = items["chart:p_2001"], items["clinician:dr_lee"]
    assert chart["slot"] == "state.task" and chart["authority"] == "state" and chart["freshness"] == doc["assembly_time"] and chart["injection_risk"] == "none"
    assert "BP" not in chart["body"] and "150/95" not in chart["body"], "the chart carries problems, medicines, allergies and labs; vitals are telemetry's or a prior note's claim"
    assert clinician["slot"] == "state.user" and doc["route_policy"]["tier_upgrades"].get("state.user") == "protected"
    included = {r["item_id"] for r in trace["included"]}
    assert {"chart:p_2001", "clinician:dr_lee", "vitals:enc_9001"} <= included


def test_the_transcript_is_untrusted_history_and_only_the_request_is_the_user(which):
    record, _ = run("02-transcript-injection", which)
    doc = record["attempts"][-1]["snapshot"]
    interaction = [i for i in items_of(doc).values() if i["slot"].startswith("interaction.") and not i["slot"].endswith("memory")]
    history = [i for i in interaction if i["slot"] == "interaction.history"]
    assert len(history) == 7 and all(i["authority"] == "untrusted" and i["injection_risk"] == "untrusted_content" for i in history)
    users = [i for i in interaction if i["authority"] == "user"]
    assert len(users) == 1 and users[0]["slot"] == "interaction.query" and users[0]["body"].startswith("Draft the SOAP note")
    injected = next(i for i in history if "oxycodone" in i["body"])
    assert injected["body"].startswith("[patient]") and injected["authority"] == "untrusted"


def test_todays_reading_wins_the_declared_fact_conflict_and_the_stale_note_loses(which):
    record, _ = run("01-followup-refill", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    assert any(g["fact"] == "vitals.bp" and set(g["items"]) == {"vitals:enc_9001", "note:p_2001:0002"} for g in doc["conflicts"])
    rec = next(c for c in trace["conflicts"] if c["group_id"] == "fact:vitals.bp")
    assert rec["decided_by"] == "policy" and rec["winner"] == "vitals:enc_9001"
    assert {r["item_id"]: r["reason"] for r in trace["excluded"]}["note:p_2001:0002"] == "conflict_lost"


def test_prior_notes_are_memory_with_variants_scoped_to_the_patient_and_a_leak_is_caught(which):
    record, _ = run("01-followup-refill", which)
    doc = record["attempts"][-1]["snapshot"]
    notes = [i for i in items_of(doc).values() if i["slot"] == "interaction.memory"]
    assert len(notes) == 3 and all(n["expires"] and n["scope"] == {"tenant": "harbor-street", "task": "p_2001"} and n["variants"][0]["lineage"] == "summarised" for n in notes)
    batch = next(b for b in doc["batches"] if b["producer"]["id"] == "ehr-notes")
    assert {e["item_id"]: e["reason"] for e in batch["excluded"]} == {"note:p_2001:0004": "expired"}
    request, drafter, _ = case("01-followup-refill")
    leaky = app.run(replace(request, faults=frozenset({"notes-ignore-patient"})), drafter, which, out=io.StringIO())
    leaked = {r["item_id"] for r in leaky["attempts"][-1]["trace"]["excluded"] if r["reason"] == "out_of_scope"}
    assert leaked == {"note:p_2002:0001"}


def test_the_capability_policy_is_the_only_source_of_tools_and_grants_by_role(which):
    record, _ = run("01-followup-refill", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    offered = {r["item_id"] for r in trace["included"] if r["slot"] == "governance.capabilities"}
    assert offered == {"cap:order_prescription_refill", "cap:add_chart_note"} == set(doc["capabilities"]["allowed_ids"])
    assert doc["capabilities"]["policy_producer"] == "capability-policy"
    assert any(e["item_id"] == "cap:order_controlled_substance" and e["reason"] == "capability_not_allowed" for b in doc["batches"] for e in b["excluded"])
    nurse, _ = run("04-nurse-visit", which)
    ntrace = nurse["attempts"][-1]["trace"]
    assert {r["item_id"] for r in ntrace["included"] if r["slot"] == "governance.capabilities"} == {"cap:add_chart_note"}
    assert ("cap:order_prescription_refill", "capability_not_allowed", "producer") in {(r["item_id"], r["reason"], r["stage"]) for r in ntrace["excluded"]}
    consult, _ = run("06-pasted-labs", which)
    cdoc = consult["attempts"][-1]["snapshot"]
    assert "capabilities" not in cdoc and "capability-policy" not in cdoc["route_policy"]["producers"]


def test_guidelines_are_one_scored_item_per_paragraph_and_the_route_requires_evidence(which):
    record, _ = run("01-followup-refill", which)
    doc = record["attempts"][-1]["snapshot"]
    evidence = [i for i in items_of(doc).values() if i["slot"] == "evidence.knowledge"]
    assert len(evidence) == 6 and all(isinstance(i["relevance"], float) for i in evidence) and len({i["id"] for i in evidence}) == 6
    refused, _ = run("05-no-guideline", which)
    trace = refused["attempts"][0]["trace"]
    assert trace["refused"] == {"bool": True, "reason": "evidence_required"} and trace["recovery"]["action"] == "request_context"
    assert all(r["reason"] == "below_threshold" for r in trace["excluded"] if r["item_id"].startswith("guide:"))
    assert refused["draft"] is None and refused["outcome"] == "needs_clinician_review" and len(refused["attempts"]) == 1


# --- budgets and escalation -------------------------------------------------------------------------------------------


def test_budgets_are_computed_and_the_pasted_report_escalates(which):
    record, _ = run("06-pasted-labs", which)
    assert [a["tier"] for a in record["attempts"]] == ["small", "large"]
    assert record["attempts"][0]["trace"]["refused"]["reason"] == "protected_content_over_budget"
    for a in record["attempts"]:
        t = common.routes()["tiers"][a["tier"]]
        assert a["snapshot"]["budget"]["input"] == t["model_context_limit"] - t["reserved_output"]
    assert record["attempts"][0]["trace"]["context"]["snapshot_digest"] != record["attempts"][1]["trace"]["context"]["snapshot_digest"]


def test_history_is_shed_before_evidence_under_pressure(which):
    request, drafter, _ = case("01-followup-refill")
    record = app.run(request, drafter, which, out=io.StringIO(), budget_input=1350)
    trace = record["attempts"][0]["trace"]
    assert not trace["refused"]["bool"]
    dropped = [r["item_id"] for r in trace["excluded"] if r["reason"] == "over_budget"]
    assert dropped and all(i.startswith("turn:") for i in dropped), dropped
    assert any(r["item_id"].startswith("note:") for r in trace["compressed"]), "a prior note goes as its summary before any guideline is omitted"


# --- the output contract and the screens ------------------------------------------------------------------------------


def test_the_output_contract_is_placed_and_the_route_declares_a_parser(which):
    record, _ = run("01-followup-refill", which)
    doc = record["attempts"][-1]["snapshot"]
    assert doc["route_policy"]["parser"] is True
    assert any(p["slot"] == "governance.output_contract" for p in doc["profile"]["placement"])
    assert record["parsed"] and set(record["parsed"]) == app.CONTRACTS["scribe"]


def test_the_prescription_guard_withholds_a_refill_the_transcript_asked_for(which):
    record, _ = run("02-transcript-injection", which)
    failed = {g["name"]: g["reason"] for g in record["guards"] if not g["ok"]}
    assert "prescription_guard" in failed and "oxycodone" in failed["prescription_guard"]
    assert record["reply"] == app.FALLBACK and record["outcome"] == "needs_clinician_review" and record["actions_queued"] == []


def test_the_vitals_guard_withholds_a_note_that_carries_the_stale_reading(which):
    record, _ = run("03-stale-vitals-in-note", which)
    assert any(g["name"] == "vitals_match_state" and not g["ok"] for g in record["guards"])
    assert record["reply"] == app.FALLBACK and record["actions_queued"] == []


def test_the_guards_as_units(which):
    guards = impl.module("guards", which)
    request, _, _ = case("01-followup-refill")
    refill = {"tool": "order_prescription_refill", "arguments": {"patient": "p_2001", "medication": "metformin", "dose": "500 mg"}}
    assert guards.prescription_guard([refill], request).ok
    assert not guards.prescription_guard([{**refill, "arguments": {**refill["arguments"], "medication": "oxycodone"}}], request).ok
    nurse, _, _ = case("04-nurse-visit")
    assert not guards.prescription_guard([refill], nurse).ok
    offered = guards.actions_were_offered([{"tool": "order_controlled_substance", "arguments": {}}], {"order_prescription_refill", "add_chart_note"})
    assert not offered.ok and "never" in offered.reason
    misnamed = guards.actions_were_offered([{"tool": "order_prescription_refill", "arguments": {"patient_id": "p_2001", "medication": "metformin", "dose": "500 mg"}}], {"order_prescription_refill"})
    assert not misnamed.ok and "schema" in misnamed.reason
    assert guards.actions_were_offered([refill], {"order_prescription_refill"}).ok
    assert guards.vitals_match_state("BP 128/82, HR 72.", "128/82", ["150/95"]).ok
    assert not guards.vitals_match_state("BP 150/95.", "128/82", ["150/95"]).ok
    assert guards.citations_were_sent(["guide:a@1#0"], {"guide:a@1#0"}).ok and not guards.citations_were_sent(["guide:a@1#1"], {"guide:a@1#0"}).ok


# --- replay and the suite ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", evals.case_names())
def test_every_attempt_replays_to_the_same_bytes(name, which):
    record, _ = run(name, which)
    for attempt in record["attempts"]:
        result = assemble(Snapshot.from_json(attempt["snapshot"]))
        assert (result.payload.decode("utf-8") if result.payload else None) == attempt["payload"]
        assert {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")} == attempt["trace"]


@pytest.mark.parametrize("name", evals.case_names())
def test_every_case_passes_its_expectations(name, which):
    record, expect = run(name, which)
    checks = evals.grade(expect, record)
    assert all(c.passed for c in checks), [f"{c.name}: {c.detail}" for c in checks if not c.passed]


def test_a_native_tool_call_is_folded_into_the_contracts_actions():
    folded = json.loads(models.fold_tool_calls('{"x": 1, "actions": []}', [("open_case", '{"client": "c_1", "category": "fraud"}')]))
    assert folded["actions"] == [{"tool": "open_case", "arguments": {"client": "c_1", "category": "fraud"}}] and folded["x"] == 1
    assert models.fold_tool_calls("not json", [("t", "{}")]) == "not json"
    assert models.fold_tool_calls("plain", []) == "plain"
