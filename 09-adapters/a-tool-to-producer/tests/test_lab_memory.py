"""Lab 2: a SQL memory table to a memory batch, and the silent bug."""

from __future__ import annotations

import pytest

import impl
from tests.conftest import assembled, codes, solution_batches


@pytest.fixture
def adapt(which):
    return impl.module("memory_adapter", which).adapt


def test_live_rows_become_items_with_their_own_scope(ada, conn, adapt):
    b = adapt(conn, ada)
    assert b["producer"] == {"id": "memory-store", "kind": "memory"}
    assert {i["id"] for i in b["items"]} == {"mem:u_ada:0005", "mem:u_ada:0007"}
    for i in b["items"]:
        assert i["slot"] == "interaction.memory" and i["authority"] == "generated" and i["expires"]
        assert i["source"].startswith("turn:") and i["scope"] == {"tenant": "w_kitewood", "user": "u_ada"}
        assert i["injection_risk"] == "untrusted_content" and i["lineage"] == "summarised"


def test_suppressed_rows_are_reported_by_id_without_text(ada, conn, adapt):
    rows = {r["item_id"]: r for r in adapt(conn, ada)["excluded"]}
    assert rows["mem:u_ada:0003"]["reason"] == "revoked" and rows["mem:u_ada:0001"]["reason"] == "expired"
    for r in rows.values():
        assert r["stage"] == "producer" and set(r) == {"item_id", "reason", "stage"}


def test_the_silent_query_loses_them_and_the_trace_cannot_tell(ada, conn, adapt):
    quiet = adapt(conn, ada, silent=True)
    assert {i["id"] for i in quiet["items"]} == {"mem:u_ada:0005", "mem:u_ada:0007"}
    assert quiet["excluded"] == [], "the WHERE clause dropped them before Python could report them"
    batches, grant = solution_batches(ada)
    others = [b for b in batches if b["producer"]["id"] != "memory-store"]
    _, loud = assembled(ada, others + [adapt(conn, ada)], grant)
    _, silent = assembled(ada, others + [quiet], grant)
    assert {"revoked", "expired"} <= set(codes(loud.trace, "producer").values())
    assert not {k for k in codes(silent.trace, "producer") if k.startswith("mem:")}, "nothing about memory reaches the trace"
    assert [r["item_id"] for r in loud.trace["included"]] == [r["item_id"] for r in silent.trace["included"]]
