"""Shared fixtures. CWA_W2_IMPL=labs runs the lab tests against your producers; the default is the solution."""

from __future__ import annotations

import pytest
from cwa import Snapshot, assemble

import common
import fixed
import freeze
import impl


@pytest.fixture
def ada():
    return freeze.request("u_ada", "How do I export the whole workspace, including attachments?", history=True)


@pytest.fixture
def cho():
    return freeze.request("u_cho", "Can I get a refund on a monthly plan?")


@pytest.fixture
def which():
    return impl.name()


def assembled(req, batches):
    doc = common.snapshot(req, batches)
    return doc, assemble(Snapshot.from_json(doc))


def codes(trace, stage: str | None = None) -> dict[str, str]:
    """item id -> reason, optionally for one stage only (producer rows travel into the trace as the producer wrote them)."""
    return {row["item_id"]: row["reason"] for row in trace["excluded"] if stage is None or row["stage"] == stage}


@pytest.fixture
def baseline(ada):
    """A valid snapshot using the given producers and the solution's, to drop one wrong item into."""
    return [fixed.app_policy(), fixed.chat_session(ada)] + [impl.module(m, "solution").__dict__[f](ada) for m, f in
            (("state", "accounts_db"), ("memory", "memory_store"), ("retrieval", "help_center_search"))]
