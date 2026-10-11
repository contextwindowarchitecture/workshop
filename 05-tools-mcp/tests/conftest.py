from __future__ import annotations

import asyncio
import json

import pytest

import impl
import scenarios


@pytest.fixture
def which():
    return impl.name()


@pytest.fixture(scope="session")
def specs():
    from tools.mcp_client import Session

    async def go():
        async with Session() as api:
            return await api.proposed()
    return asyncio.run(go())


def run(name: str) -> dict:
    return json.loads((scenarios.SCENARIOS / name / "run.json").read_text(encoding="utf-8"))


def steps(record: dict) -> list[dict]:
    return [s for inf in record["inferences"] for s in inf["steps"]]
