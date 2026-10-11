"""The migration, step by step. CWA_W3_IMPL=after runs these against your work; the default is the solution."""

from __future__ import annotations

import json

import pytest

from request import Request
from tests.conftest import codes, conversation, without

REQUIRED = {"id", "slot", "source", "source_version", "authority", "freshness", "trust", "body"}


# --- step 2: freeze and assemble --------------------------------------------------------------------------------------


def test_build_request_freezes_and_assembles(app):
    document, result = app.build_request(conversation("01-ada-export"))
    assert document["assembly_time"] == "2026-10-01T10:00:00Z"
    assert document["scope"] == {"tenant": "w_kitewood", "user": "u_ada", "session": "s_w3_ada"}
    assert {b["producer"]["id"] for b in document["batches"]} == {"app-policy", "accounts-db", "memory-store", "help-center-search", "chat-session"}
    assert not result.refused and result.payload


def test_the_same_snapshot_renders_the_same_bytes(app, context):
    document, first = app.build_request(conversation("01-ada-export"))
    second = context.assemble(json.loads(json.dumps(document)))
    assert first.payload == second.payload
    assert first.trace["result"]["hash"] == second.trace["result"]["hash"]
    assert first.trace["context"]["snapshot_digest"] == second.trace["context"]["snapshot_digest"]


# --- step 3: items with authority and source --------------------------------------------------------------------------


def test_every_item_has_an_authority_and_a_source(app):
    document, _ = app.build_request(conversation("01-ada-export"))
    for b in document["batches"]:
        for i in b["items"]:
            assert REQUIRED <= set(i), f"{i.get('id')} lacks {REQUIRED - set(i)}"
            if i["slot"] == "evidence.knowledge":
                assert "relevance" in i and i["injection_risk"] == "untrusted_content"
            if i["slot"] == "interaction.memory":
                assert "expires" in i and i["source"].startswith("turn:") and i["scope"]["user"] == "u_ada"
            if i["slot"].startswith("state."):
                assert i["authority"] == "state" and i["freshness"] == "2026-10-01T10:00:00Z"
    rows = codes(app.build_request(conversation("01-ada-export"))[1].trace, "producer")
    assert rows.get("mem:u_ada:0003") == "revoked" and rows.get("mem:u_ada:0001") == "expired"


def test_a_missing_field_is_excluded_not_guessed(app, context):
    document, _ = app.build_request(conversation("01-ada-export"))
    chunk = next(i["id"] for b in document["batches"] for i in b["items"] if i["slot"] == "evidence.knowledge")
    result = context.assemble(without(document, chunk, "relevance"))
    assert codes(result.trace)[chunk] == "missing_field:relevance"


def test_a_conflict_is_declared_and_decided_by_policy(app):
    document, result = app.build_request(conversation("02-ben-plan-conflict"))
    groups = {g["id"]: g for g in document["conflicts"]}
    assert "fact:plan" in groups and set(groups["fact:plan"]["items"]) == {"account:w_kitewood:plan", "mem:u_ben:0002"}
    record = next(c for c in result.trace["conflicts"] if c["group_id"] == "fact:plan")
    assert record["decided_by"] == "policy" and record["winner"] == "account:w_kitewood:plan"
    assert codes(result.trace)["mem:u_ben:0002"] == "conflict_lost"
    assert "account:w_kitewood:plan" in {r["item_id"] for r in result.trace["included"]}


def test_scope_catches_a_producer_leak(app):
    _, result = app.build_request(conversation("05-memory-leak"))
    leaked = {k: v for k, v in codes(result.trace, "assembler").items() if k.startswith("mem:u_ada")}
    assert leaked and set(leaked.values()) == {"out_of_scope"}
    assert "mem:u_ben:0001" in {r["item_id"] for r in result.trace["included"]}


# --- step 4: the trace, and a refusal ---------------------------------------------------------------------------------


def test_the_off_topic_question_refuses_and_nothing_is_sent(app):
    _, result = app.build_request(conversation("03-off-topic"))
    assert result.refused and result.trace["refused"]["reason"] == "evidence_required"
    assert result.trace["recovery"]["action"] == "request_context"
    assert result.payload is None and app.provider_request(result) is None


# --- step 5: the profile and the budget -------------------------------------------------------------------------------


def test_budget_input_is_the_context_limit_less_reserved_output(app, context):
    document, _ = app.build_request(conversation("01-ada-export"))
    b = document["budget"]
    assert b["input"] + b["reserved_output"] == context.policy("assembly.json")["model_context_limit"]
    assert b["reserved_output"] == context.reserved_output()


def test_the_profile_is_versioned_and_matches_the_route(app):
    document, result = app.build_request(conversation("01-ada-export"))
    profile, route = document["profile"], document["route_policy"]
    assert isinstance(profile["version"], int) and profile["version"] >= 1
    assert profile["route"] == route["route"] and profile["route_policy_version"] == route["version"]
    assert {p["slot"] for p in profile["placement"]} >= {"governance.instructions", "interaction.query"}
    assert result.trace["profile"] == {"id": profile["id"], "version": profile["version"]}


def test_history_is_capped_by_the_route(app):
    document, result = app.build_request(conversation("04-long-conversation"))
    assert document["route_policy"]["slots"]["interaction.history"]["max_tokens"]
    dropped = {k for k, v in codes(result.trace, "assembler").items() if k.startswith("turn:") and v == "over_budget"}
    assert dropped, "the oldest turns should be left out as over_budget"
    assert "turn:s_w3_long:0009" in {r["item_id"] for r in result.trace["included"]}, "the query is never dropped"


def test_the_payload_is_handed_over_unchanged(app):
    _, result = app.build_request(conversation("01-ada-export"))
    request = app.provider_request(result)
    rendered = json.loads(result.payload)
    system = [m["content"] for m in request["messages"] if m["role"] == "system"]
    rest = [m for m in request["messages"] if m["role"] != "system"]
    assert system == [e["text"] for e in rendered["system"]]
    assert rest == [{"role": m["role"], "content": m["content"]} for m in rendered["messages"]]
    assert request["max_tokens"] == result.trace["budget"]["reserved_output"]


# --- step 6: guards ---------------------------------------------------------------------------------------------------


def test_the_price_guard(guards):
    evidence = ["The Team plan costs $12 per seat per month, billed monthly."]
    assert guards.no_unverified_prices("The Team plan is $12 per seat per month.", evidence).ok
    assert not guards.no_unverified_prices("The Business plan is $24 per seat per month.", evidence).ok
    assert guards.no_unverified_prices("Exports are available on the Team and Business plans.", evidence).ok


def test_the_workspace_guard(guards):
    ada = Request(user="u_ada", session="s", asked_at="2026-10-01T10:00:00Z", question="q")
    assert guards.only_the_signed_in_workspace("Kitewood Studio is on the Business plan.", ada).ok
    assert not guards.only_the_signed_in_workspace("Larkspur Design is on the Team plan.", ada).ok
