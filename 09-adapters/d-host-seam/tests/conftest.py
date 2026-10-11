from __future__ import annotations

import json
from pathlib import Path

import pytest

import impl

HERE = Path(__file__).resolve().parents[1]


@pytest.fixture
def which():
    return impl.name()


def expected(name: str) -> tuple[dict, dict]:
    d = HERE / "expected" / name
    return json.loads((d / "snapshot.json").read_text(encoding="utf-8")), json.loads((d / "trace.json").read_text(encoding="utf-8"))
