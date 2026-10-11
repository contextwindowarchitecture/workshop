"""The application's side of MCP for one agent run: one session, the server's proposals, and calls the guard approved.
Infrastructure, not the lab."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).resolve().parent / "fernway_mcp.py"


@dataclass(frozen=True)
class Result:
    ok: bool
    value: Any


class Session:
    """async with Session(faults) as api: specs = await api.proposed(); result = await api.call(name, args)"""

    def __init__(self, faults: tuple[str, ...] = ()) -> None:
        args = [str(SERVER)] + [a for f in faults for a in ("--fault", f)]
        self._client = Client(StdioServerParameters(command=sys.executable, args=args))
        self.name, self.version = "fernway-accounts", "unknown"

    async def __aenter__(self) -> Session:
        await self._client.__aenter__()
        info = self._client.server_info
        if info:
            self.name, self.version = info.name, info.version or "unknown"
        return self

    async def __aexit__(self, kind: type[BaseException] | None, error: BaseException | None, tb: TracebackType | None) -> None:
        await self._client.__aexit__(kind, error, tb)

    async def proposed(self) -> list[dict[str, Any]]:
        listed = await self._client.list_tools()
        return [{"name": t.name, "description": t.description or "", "input_schema": t.input_schema} for t in listed.tools]

    async def call(self, name: str, arguments: dict[str, Any]) -> Result:
        outcome = await self._client.call_tool(name, arguments)
        if outcome.is_error:
            return Result(False, " ".join(getattr(b, "text", "") for b in outcome.content).strip())
        if outcome.structured_content is not None:
            return Result(True, outcome.structured_content)
        return Result(True, json.loads("".join(getattr(b, "text", "") for b in outcome.content) or "null"))
