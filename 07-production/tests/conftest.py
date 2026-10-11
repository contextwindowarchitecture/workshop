from __future__ import annotations

import asyncio
import io
import json

import pytest

import agent
import impl
import models
from request import Request

SCRIPTS = agent.Path(__file__).resolve().parents[1] / "evals" / "cases" / "scripts.json"


@pytest.fixture
def which():
    return impl.name()


@pytest.fixture(scope="session")
def status_record():
    """One recorded run: the status check, two polls, one superseded observation."""
    scripts = json.loads(SCRIPTS.read_text(encoding="utf-8"))
    request = Request(user="u_ada", session="s_test", asked_at="2026-10-01T10:00:00Z", question="Is there an incident in our region right now?")
    return asyncio.run(agent.run(request, models.ScriptedModel({"name": "scripted:test", **scripts["status-resolved"]}), out=io.StringIO()))
