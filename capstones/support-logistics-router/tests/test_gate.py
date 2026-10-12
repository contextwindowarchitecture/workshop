"""The acceptance gate. CWA_C2_IMPL=skeleton runs it against your team's modules; the default runs the reference.

Every test names the requirement it stands for. Green across the board, plus a promoted set of profiles and a lock, is
the capstone's definition of done.
"""

from __future__ import annotations

import io
import json

import pytest

import models
from cwa import Snapshot, assemble

import app
import common
import evals
import impl
from tests.conftest import case

ROUTES = {"returns", "damaged", "general"}


def run(name, which):
    request, drafter, expect = case(name)
    return app.run(request, drafter, which, out=io.StringIO()), expect


# --- intent and routing -----------------------------------------------------------------------------------------------


def test_intent_selects_the_route_before_assembly(which):
    classify = impl.module("intent", which).classify
    table = common.routes()["intents"]
    assert table[classify("I want to return these boots").route] == "returns"
    assert table[classify("The zip is broken on arrival").route] == "damaged"
    assert table[classify("Where is my parcel? Tracking says delivered").route] == "general"
    assert table[classify("Do you ship to Norway?").route] == "general"


# --- the producers and the application's duties -----------------------------------------------------------------------


def test_every_producer_the_route_lists_runs_and_only_those(which):
    record, _ = run("01-return-jacket", which)
    doc = record["attempts"][-1]["snapshot"]
    assert {b["producer"]["id"] for b in doc["batches"]} == set(doc["route_policy"]["producers"])
    assert doc["scope"] == {"tenant": "northwind", "user": "c_1001", "session": "s_c2_01", "task": "t_5001"}


def test_state_is_written_by_the_application_protected_and_current(which):
    record, _ = run("01-return-jacket", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    state = [i for b in doc["batches"] for i in b["items"] if i["slot"].startswith("state.")]
    assert {i["id"] for i in state} == {"customer:c_1001", "ticket:t_5001", "order:o_7781"}
    for i in state:
        assert i["authority"] == "state" and i["freshness"] == doc["assembly_time"] and i["injection_risk"] == "none"
    assert doc["route_policy"]["tier_upgrades"].get("state.user") == "protected"
    assert all(i["id"] in {r["item_id"] for r in trace["included"]} for i in state)


def test_no_contact_details_reach_the_model_through_state_or_memory(which):
    record, _ = run("01-return-jacket", which)
    rendered = record["attempts"][-1]["payload"].replace(" ", "")
    customer = common.customers()["c_1001"]
    assert customer["email"] not in rendered and customer["phone"].replace(" ", "") not in rendered, "the CRM note that recorded the phone number must be redacted before it reaches the model"
    notes = [i for b in record["attempts"][-1]["snapshot"]["batches"] for i in b["items"] if i["slot"] == "interaction.memory"]
    assert any(n["lineage"] == "redacted" for n in notes)


def test_crm_notes_are_memory_with_reviewed_variants_and_their_own_scope(which):
    record, _ = run("01-return-jacket", which)
    doc = record["attempts"][-1]["snapshot"]
    notes = [i for b in doc["batches"] for i in b["items"] if i["slot"] == "interaction.memory"]
    assert len(notes) == 3
    for n in notes:
        assert n["expires"] and n["source"].startswith("crm:") and n["scope"] == {"tenant": "northwind", "user": "c_1001"}
        assert n["variants"] and n["variants"][0]["lineage"] == "summarised" and len(n["variants"][0]["body"]) < len(n["body"])


def test_a_declared_fact_conflict_is_decided_by_producer_precedence(which):
    record, _ = run("01-return-jacket", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    assert any(g["fact"] == "delivery_status:o_7781" and set(g["items"]) == {"order:o_7781", "crm:c_1001:0002"} for g in doc["conflicts"])
    rec = next(c for c in trace["conflicts"] if c["group_id"] == "fact:delivery_status:o_7781")
    assert rec["decided_by"] == "policy" and rec["winner"] == "order:o_7781"
    assert {r["item_id"]: r["reason"] for r in trace["excluded"]}["crm:c_1001:0002"] == "conflict_lost"


def test_the_route_dedupes_the_identical_refund_paragraph(which):
    record, _ = run("01-return-jacket", which)
    trace = record["attempts"][-1]["trace"]
    dups = [r for r in trace["excluded"] if r["reason"] == "duplicate_content"]
    assert dups and {dups[0]["item_id"], dups[0]["duplicate_of"]} == {"kb:returns-policy@5#3", "kb:refunds-and-exchanges@4#2"}


def test_scope_catches_a_crm_leak(which):
    record, _ = run("06-crm-leak", which)
    trace = record["attempts"][-1]["trace"]
    leaked = {r["item_id"] for r in trace["excluded"] if r["reason"] == "out_of_scope"}
    assert leaked == {"crm:c_1001:0001", "crm:c_1001:0002", "crm:c_1001:0003", "crm:c_1002:0001"}


# --- routes, budgets and escalation -----------------------------------------------------------------------------------


def test_budgets_are_computed_and_the_pasted_thread_escalates(which):
    record, _ = run("04-pasted-thread", which)
    tiers = [a["tier"] for a in record["attempts"]]
    assert tiers == ["small", "large"]
    assert record["attempts"][0]["trace"]["refused"]["reason"] == "protected_content_over_budget"
    for a in record["attempts"]:
        t = common.routes()["tiers"][a["tier"]]
        assert a["snapshot"]["budget"]["input"] == t["model_context_limit"] - t["reserved_output"]
    assert record["attempts"][0]["trace"]["context"]["snapshot_digest"] != record["attempts"][1]["trace"]["context"]["snapshot_digest"]


def test_variants_are_used_before_notes_are_omitted(which):
    request, drafter, _ = case("01-return-jacket")
    record = app.run(request, drafter, which, out=io.StringIO(), budget_input=950)
    trace = record["attempts"][0]["trace"]
    assert not trace["refused"]["bool"]
    assert any(r["item_id"].startswith("crm:") for r in trace["compressed"]), "CRM notes compress to their summaries first"


# --- the output contract and the screens ------------------------------------------------------------------------------


def test_the_output_contract_is_placed_and_the_route_declares_a_parser(which):
    record, _ = run("02-damaged-tent", which)
    doc = record["attempts"][-1]["snapshot"]
    assert doc["route_policy"]["parser"] is True
    assert any(p["slot"] == "governance.output_contract" for p in doc["profile"]["placement"])
    assert record["parsed"] and set(record["parsed"]) == {"reply", "next_stage", "citations"}


def test_the_pii_screen_withholds_a_draft_with_a_phone_number(which):
    record, _ = run("05-pii-in-draft", which)
    assert any(g["name"] == "pii_screen" and not g["ok"] for g in record["guards"])
    assert record["reply"] == app.FALLBACK and record["next_stage"] == "needs_agent"


def test_citations_must_have_been_sent(which):
    guards = impl.module("guards", which)
    assert guards.citations_were_sent(["kb:shipping@7#2"], {"kb:shipping@7#2", "kb:shipping@7#1"}).ok
    assert not guards.citations_were_sent(["kb:shipping@7#3"], {"kb:shipping@7#2"}).ok


def test_the_other_customer_screen(which):
    guards = impl.module("guards", which)
    request, _, _ = case("03-where-is-order")
    assert guards.only_this_customer_and_order("Your gloves from order o_7815 are on their way.", request).ok
    assert not guards.only_this_customer_and_order("Like Maya Lindqvist's jacket, your order o_7781 shows delivered.", request).ok


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
