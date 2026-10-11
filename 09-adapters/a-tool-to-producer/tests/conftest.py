from __future__ import annotations

import pytest
from cwa import Snapshot, assemble

import common
import impl
import run
from tools import llama_retriever, mcp_client, memory_db


@pytest.fixture
def ada():
    return run.request("u_ada", "How do I export the whole workspace, including attachments?")


@pytest.fixture
def ben():
    return run.request("u_ben", "Who are the billing admins?")


@pytest.fixture
def which():
    return impl.name()


@pytest.fixture
def hits(ada):
    return llama_retriever.retrieve(ada.question, common.policy("assembly.json")["retrieval"]["top_k"])


@pytest.fixture
def conn():
    return memory_db.connect()


@pytest.fixture(scope="session")
def mcp_session():
    """One real server session for the whole test run: account, then status twice, then a bad workspace."""
    calls = run.scripted_calls("u_ada", ["account", "status", "status"]) + [mcp_client.Call("get_account", {"workspace": "w_nope"}, "2026-10-01T10:00:04Z")]
    return mcp_client.session(calls)


def assembled(req, batches, grant=None):
    doc = common.snapshot(req, batches, grant)
    return doc, assemble(Snapshot.from_json(doc))


def codes(trace, stage=None):
    return {r["item_id"]: r["reason"] for r in trace["excluded"] if stage is None or r["stage"] == stage}


def solution_batches(req, calls=()):
    """A valid set of batches from the solution, to swap one adapter's output into."""
    doc = run.build(req, list(calls), "solution")
    return doc["batches"], doc.get("capabilities")
