from __future__ import annotations

import json

import pytest

import evals
import impl
import models
from common import Request


@pytest.fixture
def which():
    return impl.name()


def case(name: str) -> tuple[Request, models.ScriptedDrafter, dict]:
    d = evals.CASES / name
    return (Request.load(d / "conversation.json"),
            models.ScriptedDrafter(json.loads((d / "draft.json").read_text(encoding="utf-8")), f"scripted:{name}"),
            json.loads((d / "expect.json").read_text(encoding="utf-8")))
