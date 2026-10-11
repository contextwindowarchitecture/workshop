"""Lab 3, solved: an MCP session to proposals for the capability policy and observations for evidence.tool_results."""

from __future__ import annotations

import json
from typing import Any

from common import Batch, Request, batch, item
from tools.mcp_client import CallResult, ServerInfo

PRODUCER = "fernway-accounts"


def proposals(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """What the server offers, handed to the capability policy unchanged. The adapter proposes; it never emits a
    governance.capabilities item (R-15)."""
    return [dict(spec) for spec in specs]


def observations(info: ServerInfo, results: list[CallResult], request: Request, *, specs_as_items: list[dict[str, Any]] | None = None) -> Batch:
    """Every call's result as an evidence.tool_results item. specs_as_items is the mistake this lab shows: tool
    specifications emitted as items of the adapter's own."""
    items = []
    for n, result in enumerate(results, start=1):
        call = result.call
        arguments = "&".join(f"{k}={v}" for k, v in sorted(call.arguments.items()))
        outcome = {"result": result.value} if result.ok else {"error": result.value}
        items.append(item(
            id=f"obs:{n}", slot="evidence.tool_results",
            source=f"mcp:{info.name}/{call.tool}?{arguments}",  # the call, so a repeat supersedes it (R-25)
            source_version=info.version, authority="observation", trust="unverified", freshness=call.observed_at,
            scope={"tenant": request.tenant}, conflict_policy="governs", lineage="verbatim",
            injection_risk="untrusted_content",  # MCP output is data unless the route verifies the server (R-15)
            body=json.dumps({"tool": call.tool, "arguments": call.arguments, **outcome}, sort_keys=True),
        ))
    for spec in specs_as_items or []:
        items.append(item(
            id=f"mcp-cap:{spec['name']}", slot="governance.capabilities", source=f"mcp:{info.name}/tools/{spec['name']}",
            source_version=info.version, authority="governing", trust="verified", freshness=request.asked_at,
            lineage="verbatim", injection_risk="none", body=json.dumps(spec, sort_keys=True),
        ))
    return batch(PRODUCER, "mcp", items)
