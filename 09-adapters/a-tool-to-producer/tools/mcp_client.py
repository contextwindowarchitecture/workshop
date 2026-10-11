"""The application's side of MCP, as plain functions: list what the server proposes and make a scripted set of calls.

Infrastructure, not the lab. One server process per session; the official SDK over stdio. Every call carries the
observed_at the application assigns from its own clock, so a recorded session replays to the same items.

    specs, results = mcp_client.session([Call("get_account", {"workspace": "w_kitewood"}, "2026-10-01T10:00:02Z")])
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).resolve().parent / "fernway_mcp.py"


@dataclass(frozen=True)
class Call:
    tool: str
    arguments: dict[str, Any]
    observed_at: str


@dataclass(frozen=True)
class CallResult:
    call: Call
    ok: bool
    value: Any  # the structured result, or the error text


@dataclass(frozen=True)
class ServerInfo:
    name: str
    version: str


def session(calls: list[Call]) -> tuple[ServerInfo, list[dict[str, Any]], list[CallResult]]:
    """Start the server, read its info and tool proposals, make the calls in order, stop the server."""
    return asyncio.run(_session(calls))


async def _session(calls: list[Call]) -> tuple[ServerInfo, list[dict[str, Any]], list[CallResult]]:
    client = Client(StdioServerParameters(command=sys.executable, args=[str(SERVER)]))
    async with client:
        stamp = client.server_info  # the server's own name and version, which the adapter puts in source_version
        info = ServerInfo(stamp.name if stamp else "unknown", (stamp.version if stamp else None) or "unknown")
        listed = await client.list_tools()
        specs = [{"name": t.name, "description": t.description or "", "input_schema": t.input_schema} for t in listed.tools]
        results = []
        for call in calls:
            outcome = await client.call_tool(call.tool, call.arguments)
            if outcome.is_error:
                results.append(CallResult(call, False, " ".join(getattr(b, "text", "") for b in outcome.content).strip()))
            elif outcome.structured_content is not None:
                results.append(CallResult(call, True, outcome.structured_content))
            else:
                results.append(CallResult(call, True, json.loads("".join(getattr(b, "text", "") for b in outcome.content) or "null")))
        return info, specs, results
