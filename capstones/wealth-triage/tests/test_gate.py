"""The acceptance gate. CWA_C3_IMPL=skeleton runs it against your team's modules; the default runs the reference.

Every test names the requirement it stands for. Green across the board, plus a promoted pair of profiles and a lock, is
the capstone's definition of done.
"""

from __future__ import annotations

import io
import json

import pytest
from cwa import Snapshot, assemble

import app
import cache
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
    assert table[classify("I didn't make this transfer").route] == "triage"
    assert table[classify("My card was stolen yesterday").route] == "triage"
    assert table[classify("What is my ACME position worth?").route] == "portfolio"
    assert table[classify("Please sell 500 ACME").route] == "portfolio"


# --- the producers and the application's duties -----------------------------------------------------------------------


def test_every_producer_the_route_lists_runs_and_only_those(which):
    record, _ = run("01-holdings-question", which)
    doc = record["attempts"][-1]["snapshot"]
    assert {b["producer"]["id"] for b in doc["batches"]} == set(doc["route_policy"]["producers"])
    assert doc["scope"] == {"tenant": "larkbridge", "user": "c_3001", "session": "s_c3_01", "task": "acct_7701"}


def test_client_state_is_protected_and_carries_no_identifiers(which):
    record, _ = run("01-holdings-question", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    client = items_of(doc)["client:c_3001"]
    c = common.clients()["c_3001"]
    assert client["slot"] == "state.user" and client["authority"] == "state" and doc["route_policy"]["tier_upgrades"]["state.user"] == "protected"
    payload = record["attempts"][-1]["payload"]
    assert c["iban"] not in payload and "acct_7701" not in client["body"], "the model never needs an account identifier"
    assert "client:c_3001" in {r["item_id"] for r in trace["included"]}


def test_the_ledger_is_current_state_and_the_vendor_estimate_is_untrusted_evidence(which):
    record, _ = run("01-holdings-question", which)
    doc = record["attempts"][-1]["snapshot"]
    items = items_of(doc)
    ledger, vendor = items["ledger:acct_7701"], items["vendor-position:acct_7701:ACME"]
    assert ledger["slot"] == "state.task" and ledger["authority"] == "state" and ledger["trust"] == "verified"
    assert vendor["slot"] == "evidence.tool_results" and vendor["authority"] == "observation" and vendor["injection_risk"] == "untrusted_content"
    assert "1000 units settled" in ledger["body"] and "1200 units" in vendor["body"]


def test_the_ledger_wins_the_declared_position_conflict(which):
    record, _ = run("01-holdings-question", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    assert any(g["fact"] == "position.ACME" and set(g["items"]) == {"ledger:acct_7701", "vendor-position:acct_7701:ACME"} for g in doc["conflicts"])
    rec = next(c for c in trace["conflicts"] if c["group_id"] == "fact:position.ACME")
    assert rec["decided_by"] == "policy" and rec["winner"] == "ledger:acct_7701"
    assert {r["item_id"]: r["reason"] for r in trace["excluded"]}["vendor-position:acct_7701:ACME"] == "conflict_lost"


def test_the_risk_screen_is_state_the_application_wrote_and_gates_the_capabilities(which):
    producers = impl.module("producers", which)
    quiet, _, _ = case("01-holdings-question")
    fraud, _, _ = case("05-fraud-report")
    assert producers.risk_level(quiet)[0] == "low"
    level, signals = producers.risk_level(fraud)
    assert level == "critical" and len(signals) >= 2
    record, _ = run("05-fraud-report", which)
    doc, trace = record["attempts"][-1]["snapshot"], record["attempts"][-1]["trace"]
    risk = items_of(doc)["risk:s_c3_05"]
    assert risk["slot"] == "state.task" and risk["authority"] == "state" and "critical" in risk["body"]
    offered = {r["item_id"] for r in trace["included"] if r["slot"] == "governance.capabilities"}
    assert offered == {"cap:open_case"}
    withheld = {(r["item_id"], r["stage"]) for r in trace["excluded"] if r["reason"] == "capability_not_allowed"}
    assert {("cap:place_trade", "producer"), ("cap:schedule_advisor_call", "producer"), ("cap:transfer_funds", "producer")} <= withheld


def test_the_capability_policy_grants_trading_by_mandate(which):
    advisory, _ = run("03-advisory-sell-request", which)
    self_directed, _ = run("04-self-directed-sell", which)
    offered = lambda rec: {r["item_id"] for r in rec["attempts"][-1]["trace"]["included"] if r["slot"] == "governance.capabilities"}
    assert "cap:place_trade" not in offered(advisory) and "cap:place_trade" in offered(self_directed)
    for rec in (advisory, self_directed):
        doc = rec["attempts"][-1]["snapshot"]
        assert set(doc["capabilities"]["allowed_ids"]) == offered(rec) and doc["capabilities"]["policy_producer"] == "capability-policy"
        assert all(i["slot"] != "governance.capabilities" for b in doc["batches"] if b["producer"]["kind"] != "capability_policy" for i in b["items"])


def test_articles_are_one_scored_item_per_paragraph_and_the_route_requires_evidence(which):
    record, _ = run("01-holdings-question", which)
    doc = record["attempts"][-1]["snapshot"]
    evidence = [i for i in items_of(doc).values() if i["slot"] == "evidence.knowledge"]
    assert len(evidence) == 5 and all(isinstance(i["relevance"], float) for i in evidence)
    request, drafter, _ = case("01-holdings-question")
    from dataclasses import replace

    refused = app.run(replace(request, question="Hmm?"), drafter, which, out=io.StringIO())
    trace = refused["attempts"][0]["trace"]
    assert trace["refused"]["reason"] == "evidence_required" and refused["draft"] is None and refused["outcome"] == "needs_advisor"


# --- budgets, escalation and placement --------------------------------------------------------------------------------


def test_budgets_are_computed_and_the_pasted_statement_escalates(which):
    record, _ = run("06-pasted-statement", which)
    assert [a["tier"] for a in record["attempts"]] == ["small", "large"]
    assert record["attempts"][0]["trace"]["refused"]["reason"] == "protected_content_over_budget"
    for a in record["attempts"]:
        t = common.routes()["tiers"][a["tier"]]
        assert a["snapshot"]["budget"]["input"] == t["model_context_limit"] - t["reserved_output"]


def test_the_cache_first_profile_reuses_more_blocks_than_history_first(which):
    conversation = json.loads((cache.HERE / "conversations" / "four-turns.json").read_text(encoding="utf-8"))
    requests = cache.turns_of(conversation)
    committed = cache.measure(requests, "portfolio", which)
    alternative = cache.measure(requests, "portfolio", which, cache.history_first(common.policy("portfolio", "profile.json")))
    assert committed["turns"] == 4 and committed["reuse"] >= 0.5 and committed["reuse"] > alternative["reuse"]
    assert all(p["shared"] >= 7 for p in committed["pairs"]), "the system entries, client, ledger, risk, tools and contract are stable across the session"


# --- the output contracts and the screens -----------------------------------------------------------------------------


def test_the_contracts_are_placed_and_both_routes_declare_a_parser(which):
    for name, route in (("01-holdings-question", "portfolio"), ("05-fraud-report", "triage")):
        record, _ = run(name, which)
        doc = record["attempts"][-1]["snapshot"]
        assert doc["route_policy"]["parser"] is True and any(p["slot"] == "governance.output_contract" for p in doc["profile"]["placement"])
        assert record["parsed"] and set(record["parsed"]) == app.CONTRACTS[route]


def test_figures_are_held_to_the_ledger(which):
    record, _ = run("02-vendor-figure-in-answer", which)
    failed = {g["name"]: g["reason"] for g in record["guards"] if not g["ok"]}
    assert "figures_match_ledger" in failed and "1200" in failed["figures_match_ledger"]
    assert record["reply"] == app.FALLBACK and record["outcome"] == "needs_advisor"


def test_an_order_the_policy_did_not_offer_is_withheld(which):
    record, _ = run("03-advisory-sell-request", which)
    assert any(g["name"] == "actions_were_offered" and not g["ok"] for g in record["guards"])
    assert record["actions_queued"] == [] and record["outcome"] == "needs_advisor"


def test_the_guards_as_units(which):
    guards = impl.module("guards", which)
    request, _, _ = case("04-self-directed-sell")
    sell = lambda q, sym="ACME": {"tool": "place_trade", "arguments": {"client": "c_3002", "symbol": sym, "side": "sell", "quantity": q}}
    assert guards.trade_guard([sell(500)], request).ok
    assert not guards.trade_guard([sell(1500)], request).ok and not guards.trade_guard([sell(10, "GLOBX")], request).ok
    assert guards.figures_match_ledger([{"symbol": "ACME", "units": 1000, "value": 42100.0}], request).ok
    assert not guards.figures_match_ledger([{"symbol": "ACME", "units": 1200, "value": 1.0}], request).ok
    assert guards.figures_match_ledger([{"symbol": "CASH", "units": None, "value": 3100.0}], request).ok and not guards.figures_match_ledger([{"symbol": "CASH", "units": 0, "value": 99.0}], request).ok
    assert not guards.no_account_identifiers("Your IBAN GB94 LBWX 6016 1331 7700 02 is on file.").ok and guards.no_account_identifiers("You hold 1,000 ACME.").ok
    assert guards.urgency_covers_risk("critical", "critical").ok and not guards.urgency_covers_risk("normal", "elevated").ok and not guards.urgency_covers_risk("urgent", "low").ok
    never = guards.actions_were_offered([{"tool": "transfer_funds", "arguments": {}}], {"open_case"})
    assert not never.ok and "never moves money" in never.reason
    misnamed = guards.actions_were_offered([{"tool": "place_trade", "arguments": {"client": "c_3002", "symbol": "ACME", "side": "sell", "quantity": "500"}}], {"place_trade"})
    assert not misnamed.ok and "schema" in misnamed.reason and guards.actions_were_offered([sell(500)], {"place_trade"}).ok
    assert guards.citations_were_sent(["kb:a@1#0"], {"kb:a@1#0"}).ok and not guards.citations_were_sent(["kb:a@1#1"], {"kb:a@1#0"}).ok


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
