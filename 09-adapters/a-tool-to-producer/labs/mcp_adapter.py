"""Lab 3: wrap an MCP server as the fernway-accounts producer, and keep its tool specifications out of governance.

The tool is tools/fernway_mcp.py, driven by tools/mcp_client.py, which gives you three things from one session: a
ServerInfo (name, version), the server's tool specifications (name, description, input_schema), and a CallResult for
each scripted call (call.tool, call.arguments, call.observed_at, ok, value). Write both functions until
`CWA_W9A_IMPL=labs uv run pytest tests/test_lab_mcp.py` passes.

proposals(specs): return the specifications for the capability policy, unchanged. An MCP adapter proposes tools; the
application's capability policy, and only it, emits governance.capabilities (R-15). The policy pins each schema by
hash and uses its own description, so what you hand over is the server's claim, not an offer to the model.

observations(info, results, request, specs_as_items=None): one evidence.tool_results item per call:

1. id = f"obs:{n}" counting from 1 in call order.
2. source = f"mcp:{info.name}/{call.tool}?{arguments}" with the arguments as sorted key=value pairs joined by &.
   The source is the call, so when the same call is made again the route's supersede: source keeps the newest
   observation and excludes the older one with superseded_by (R-25).
3. source_version = info.version; authority observation; trust unverified; freshness = call.observed_at;
   scope = {"tenant": request.tenant}; conflict_policy governs; lineage verbatim; injection_risk
   untrusted_content, because MCP output is data unless the route verifies the server (R-15).
4. body = JSON of {"tool", "arguments", "result"} on success or {"tool", "arguments", "error"} on an error, with
   sort_keys=True. An error is an observation too.
5. Return common.batch("fernway-accounts", "mcp", items).

specs_as_items is the mistake this lab makes visible. When it is a list of specs, also emit each as a
governance.capabilities item from this adapter with id f"mcp-cap:{name}" (authority governing, trust verified,
injection_risk none, body the spec as JSON). run.py --fault specs-as-items passes it. Watch what the assembler does with those items, then read
R-15 for why, and note which of two codes it recorded and what would change it.
"""

from __future__ import annotations

from typing import Any

from common import Batch, Request
from tools.mcp_client import CallResult, ServerInfo


def proposals(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise NotImplementedError("Lab 3: see the module docstring")


def observations(info: ServerInfo, results: list[CallResult], request: Request, *, specs_as_items: list[dict[str, Any]] | None = None) -> Batch:
    raise NotImplementedError("Lab 3: see the module docstring")
