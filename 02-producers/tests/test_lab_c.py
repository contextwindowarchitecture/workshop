"""Lab C: the state producer."""

from __future__ import annotations

import pytest

import impl
from tests.conftest import assembled, codes


@pytest.fixture
def accounts(which):
    return impl.module("state", which).accounts_db


def test_one_typed_item_per_fact(ada, accounts):
    b = accounts(ada)
    assert b["producer"] == {"id": "accounts-db", "kind": "state"}
    by_id = {i["id"]: i for i in b["items"]}
    assert set(by_id) == {"account:w_kitewood:plan", "account:w_kitewood:u_ada"}
    assert "Business" in by_id["account:w_kitewood:plan"]["body"]
    assert by_id["account:w_kitewood:plan"]["scope"] == {"tenant": "w_kitewood"}
    assert by_id["account:w_kitewood:u_ada"]["scope"] == {"tenant": "w_kitewood", "user": "u_ada"}
    for i in by_id.values():
        assert i["slot"] == "state.user" and i["authority"] == "state" and i["trust"] == "verified"
        assert i["lineage"] == "extracted" and i["injection_risk"] == "none"
        assert i["source"].startswith("accounts-db:") and i["source_version"].isdigit()


def test_freshness_is_the_read_time(ada, accounts):
    for i in accounts(ada)["items"]:
        assert i["freshness"] == ada.asked_at
    stale = ada.__class__(**{**ada.__dict__, "account_read_at": "2026-10-01T09:50:00Z"})
    for i in accounts(stale)["items"]:
        assert i["freshness"] == "2026-10-01T09:50:00Z"


def test_a_cached_read_older_than_the_route_allows_is_stale_state(ada, accounts, baseline):
    stale = ada.__class__(**{**ada.__dict__, "account_read_at": "2026-10-01T09:50:00Z"})
    batches = [b for b in baseline if b["producer"]["id"] != "accounts-db"] + [accounts(stale)]
    _, result = assembled(stale, batches)
    assert codes(result.trace)["account:w_kitewood:plan"] == "stale_state"
    fresh = [b for b in baseline if b["producer"]["id"] != "accounts-db"] + [accounts(ada)]
    _, result = assembled(ada, fresh)
    assert "account:w_kitewood:plan" in {r["item_id"] for r in result.trace["included"]}
