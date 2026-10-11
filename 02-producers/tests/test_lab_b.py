"""Lab B: the memory producer."""

from __future__ import annotations

import pytest

import impl
from tests.conftest import assembled, codes


@pytest.fixture
def store(which):
    return impl.module("memory", which).memory_store


def test_live_memories_are_items_with_expires_and_scope(ada, store):
    b = store(ada)
    assert b["producer"] == {"id": "memory-store", "kind": "memory"}
    ids = {i["id"] for i in b["items"]}
    assert ids == {"mem:u_ada:0005", "mem:u_ada:0007"}
    for i in b["items"]:
        assert i["slot"] == "interaction.memory" and i["authority"] == "generated"
        assert i["expires"] and i["source"].startswith("turn:")
        assert i["scope"] == {"tenant": "w_kitewood", "user": "u_ada"}
        assert i["injection_risk"] == "untrusted_content" and i["lineage"] == "summarised"


def test_expired_and_revoked_are_reported_without_their_text(ada, store):
    b = store(ada)
    rows = {r["item_id"]: r for r in b["excluded"]}
    assert rows["mem:u_ada:0003"]["reason"] == "revoked"
    assert rows["mem:u_ada:0001"]["reason"] == "expired"
    for r in rows.values():
        assert r["stage"] == "producer" and "body" not in r and "text" not in r


def test_other_users_are_not_read_at_all(cho, store):
    b = store(cho)
    assert {i["id"] for i in b["items"]} == {"mem:u_cho:0001"}
    assert {r["item_id"] for r in b["excluded"]} == {"mem:u_cho:0002", "mem:u_cho:0003"}


def test_producer_rows_reach_the_trace_and_scope_catches_a_leak(ada, store, baseline):
    batches = [b for b in baseline if b["producer"]["id"] != "memory-store"] + [store(ada)]
    _, result = assembled(ada, batches)
    assert codes(result.trace)["mem:u_ada:0003"] == "revoked"
    leaky = ada.__class__(**{**ada.__dict__, "faults": frozenset({"memory-store-ignores-user"})})
    batches = [b for b in baseline if b["producer"]["id"] != "memory-store"] + [store(leaky)]
    _, result = assembled(leaky, batches)
    assert codes(result.trace).get("mem:u_ben:0001") == "out_of_scope"
