from __future__ import annotations

import json

import pytest

import impl
import scenarios
from request import Request


@pytest.fixture
def which():
    return impl.name()


def conversation(name: str) -> Request:
    return Request.load(scenarios.SCENARIOS / name / "conversation.json")


def trace(name: str, attempt: str) -> dict:
    return json.loads((scenarios.SCENARIOS / name / f"{attempt}.trace.json").read_text(encoding="utf-8"))
