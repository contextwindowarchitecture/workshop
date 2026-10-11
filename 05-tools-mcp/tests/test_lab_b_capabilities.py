"""Lab B: the capability policy file. CWA_W5_IMPL=labs checks yours."""

from __future__ import annotations

import capability_policy


def offered(specs, role, which):
    batch, grant, granted = capability_policy.offer(specs, role, "2026-10-01T10:00:01Z", which=which)
    return {i["id"] for i in batch["items"]}, {r["item_id"] for r in batch["excluded"]}, grant, granted


def test_delete_workspace_is_never_offered_to_anyone(specs, which):
    for role in ("Owner", "Admin", "Member"):
        items, excluded, _, _ = offered(specs, role, which)
        assert "cap:delete_workspace" not in items and "cap:delete_workspace" in excluded
    assert "delete_workspace" in capability_policy.policy(which).get("never", {})


def test_a_member_is_not_offered_list_members_or_plan_changes(specs, which):
    items, excluded, _, _ = offered(specs, "Member", which)
    assert items == {"cap:get_account", "cap:get_service_status"}
    assert {"cap:list_members", "cap:request_plan_change"} <= excluded


def test_only_owners_may_change_the_plan(specs, which):
    assert "cap:request_plan_change" in offered(specs, "Owner", which)[0]
    assert "cap:request_plan_change" not in offered(specs, "Admin", which)[0]


def test_workspace_arguments_are_scoped_to_the_tenant(specs, which):
    _, _, _, granted = offered(specs, "Owner", which)
    for name in ("get_account", "list_members", "request_plan_change"):
        assert granted[name].scope == {"workspace": "tenant"}, name


def test_the_grant_names_exactly_the_offered_ids_and_pins_the_schemas(specs, which):
    items, _, grant, _ = offered(specs, "Owner", which)
    assert set(grant["allowed_ids"]) == items
    rules = capability_policy.policy(which)["grants"]
    for spec in specs:
        if spec["name"] in rules:
            assert rules[spec["name"]]["schema_sha256"] == capability_policy.schema_sha256(spec["input_schema"])
