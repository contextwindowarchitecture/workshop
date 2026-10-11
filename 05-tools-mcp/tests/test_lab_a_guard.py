"""Lab A: the guard. CWA_W5_IMPL=labs runs these against yours."""

from __future__ import annotations

import pytest

import capability_policy
import impl

SCOPE = {"tenant": "w_kitewood", "user": "u_ada", "session": "s", "task": "t"}


@pytest.fixture
def granted(specs):
    _, _, granted = capability_policy.offer(specs, "Owner", "2026-10-01T10:00:01Z", which="solution")
    return granted


@pytest.fixture
def authorize(which):
    return impl.module("guard", which).authorize


def test_an_offered_call_with_matching_arguments_is_approved(authorize, granted):
    d = authorize("get_account", {"workspace": "w_kitewood"}, granted, SCOPE)
    assert d.approved


def test_a_tool_not_offered_is_denied_and_the_never_reason_is_given(authorize, granted):
    d = authorize("delete_workspace", {"workspace": "w_kitewood"}, granted, SCOPE)
    assert not d.approved and "not offered" in d.reason and "restored" in d.reason


def test_arguments_must_match_the_schema(authorize, granted):
    assert not authorize("get_account", {"workspce": "w_kitewood"}, granted, SCOPE).approved
    assert not authorize("get_account", "w_kitewood", granted, SCOPE).approved
    assert not authorize("request_plan_change", {"workspace": "w_kitewood"}, granted, SCOPE).approved


def test_arguments_must_name_the_signed_in_workspace(authorize, granted):
    d = authorize("get_account", {"workspace": "w_larkspur"}, granted, SCOPE)
    assert not d.approved and "w_larkspur" in d.reason and "w_kitewood" in d.reason
    assert authorize("request_plan_change", {"workspace": "w_kitewood", "plan": "Team"}, granted, SCOPE).approved
    assert not authorize("request_plan_change", {"workspace": "w_larkspur", "plan": "Team"}, granted, SCOPE).approved


def test_nothing_is_offered_on_the_final_turn(authorize, specs):
    _, grant, granted = capability_policy.offer(specs, "Owner", "2026-10-01T10:00:01Z", final_turn=True, which="solution")
    assert granted == {} and grant["allowed_ids"] == []
    assert not authorize("get_account", {"workspace": "w_kitewood"}, granted, SCOPE).approved
