from __future__ import annotations

import copy

import pytest

import impl
import scenarios
from request import Request


@pytest.fixture
def which():
    return impl.name()


@pytest.fixture
def app(which):
    return impl.module("app", which)


@pytest.fixture
def context(which):
    return impl.module("context", which)


@pytest.fixture
def guards(which):
    return impl.module("guards", which)


def conversation(name: str) -> Request:
    return Request.load(scenarios.SCENARIOS / name / "conversation.json")


def codes(trace, stage=None):
    return {r["item_id"]: r["reason"] for r in trace["excluded"] if stage is None or r["stage"] == stage}


def without(document, item_id, field):
    doc = copy.deepcopy(document)
    for b in doc["batches"]:
        for i in b["items"]:
            if i["id"] == item_id:
                del i[field]
    return doc
