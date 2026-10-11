"""The MCP server you already run: Fernway account and status data over stdio, through the official MCP SDK.

This is the tool being wrapped, not the lab. It proposes three tools and answers calls. It decides nothing about who
may call them, and it does not know what the model will be told about them: the capability policy does both (R-15).
Service status follows a timeline per process, so the second call about a region sees a later state than the first,
the way a real status API would between two polls.

    uv run python tools/fernway_mcp.py       # started by tools/mcp_client.py, one process per session
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from fernway import ACCOUNTS  # noqa: E402

SERVER_NAME = "fernway-accounts"
SERVER_VERSION = "1.2.0"
server = MCPServer(SERVER_NAME, version=SERVER_VERSION, instructions="Accounts and service status of Fernway workspaces.", log_level="WARNING")
accounts: dict[str, Any] = json.loads(ACCOUNTS.read_text(encoding="utf-8"))
STATUS_TIMELINE = {
    "EU": [{"status": "incident", "note": "Elevated webhook delivery latency since 09:41 UTC."},
           {"status": "resolved", "note": "Webhook delivery latency back to normal at 10:03 UTC."}],
    "US": [{"status": "operational", "note": "All systems operational."}],
}
_polls: dict[str, int] = {}


@server.tool()
def get_account(workspace: str) -> dict[str, Any]:
    """Get a workspace's plan, billing cycle, seats and data region."""
    if workspace not in accounts["workspaces"]:
        raise ToolError(f"no workspace {workspace}")
    return {"workspace": workspace, **accounts["workspaces"][workspace]}


@server.tool()
def list_members(workspace: str) -> dict[str, Any]:
    """List a workspace's members with their role and whether they administer billing."""
    if workspace not in accounts["workspaces"]:
        raise ToolError(f"no workspace {workspace}")
    members = [{"user": uid, "name": u["name"], "role": u["role"], "billing_admin": u["billing_admin"]}
               for uid, u in sorted(accounts["users"].items()) if u["workspace"] == workspace]
    return {"workspace": workspace, "members": members}


@server.tool()
def get_service_status(region: str) -> dict[str, Any]:
    """Current service status for a data region (EU or US)."""
    if region not in STATUS_TIMELINE:
        raise ToolError(f"unknown region {region}")
    n = _polls.get(region, 0)
    _polls[region] = n + 1
    timeline = STATUS_TIMELINE[region]
    return {"region": region, **timeline[min(n, len(timeline) - 1)]}


if __name__ == "__main__":
    server.run("stdio")
