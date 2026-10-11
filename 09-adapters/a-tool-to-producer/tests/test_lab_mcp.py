"""Lab 3: an MCP session to proposals and observations."""

from __future__ import annotations

import json

import pytest

import capability_policy
import impl
from tests.conftest import assembled, codes, solution_batches


@pytest.fixture
def mcp(which):
    return impl.module("mcp_adapter", which)


def test_proposals_are_the_servers_specs_unchanged(mcp_session, mcp):
    _, specs, _ = mcp_session
    assert mcp.proposals(specs) == specs
    assert {s["name"] for s in specs} == {"get_account", "list_members", "get_service_status"}


def test_one_observation_per_call_keyed_by_the_call(ada, mcp_session, mcp):
    info, _, results = mcp_session
    b = mcp.observations(info, results, ada)
    assert b["producer"] == {"id": "fernway-accounts", "kind": "mcp"}
    assert [i["id"] for i in b["items"]] == ["obs:1", "obs:2", "obs:3", "obs:4"]
    assert b["items"][0]["source"] == "mcp:fernway-accounts/get_account?workspace=w_kitewood"
    assert b["items"][1]["source"] == b["items"][2]["source"] == "mcp:fernway-accounts/get_service_status?region=EU"
    for i, r in zip(b["items"], results):
        assert i["slot"] == "evidence.tool_results" and i["authority"] == "observation"
        assert i["freshness"] == r.call.observed_at and i["source_version"] == info.version
        assert i["injection_risk"] == "untrusted_content" and i["scope"] == {"tenant": "w_kitewood"}
        body = json.loads(i["body"])
        assert body["tool"] == r.call.tool and body["arguments"] == r.call.arguments
        assert ("result" in body) == r.ok and ("error" in body) == (not r.ok)


def test_the_repeated_call_is_superseded_and_the_error_is_kept(ada, mcp_session, mcp):
    info, specs, results = mcp_session
    batches, _ = solution_batches(ada)
    caps, grant = capability_policy.offer(mcp.proposals(specs), ada.role, ada.asked_at)
    batches = [b for b in batches if b["producer"]["id"] not in ("fernway-accounts", "capability-policy")] + [caps, mcp.observations(info, results, ada)]
    _, result = assembled(ada, batches, grant)
    rows = {r["item_id"]: r for r in result.trace["excluded"]}
    assert rows["obs:2"]["reason"] == "superseded" and rows["obs:2"]["superseded_by"] == "obs:3"
    included = {r["item_id"] for r in result.trace["included"]}
    assert {"obs:1", "obs:3", "obs:4", "cap:get_account", "cap:list_members", "cap:get_service_status"} <= included


def test_specs_emitted_as_items_never_reach_the_model(ada, mcp_session, mcp):
    info, specs, results = mcp_session
    batches, _ = solution_batches(ada)
    caps, grant = capability_policy.offer(mcp.proposals(specs), ada.role, ada.asked_at)
    batches = [b for b in batches if b["producer"]["id"] not in ("fernway-accounts", "capability-policy")] + [caps, mcp.observations(info, results, ada, specs_as_items=specs)]
    _, result = assembled(ada, batches, grant)
    got = codes(result.trace, "assembler")
    for s in specs:
        assert got[f"mcp-cap:{s['name']}"] == "producer_slot_not_allowed", got
    payload = json.loads(result.payload)
    assert len(payload["tools"]) == 3, "only the capability policy's three tools render"
