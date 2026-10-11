"""Lab B, solved: a CWA trace as span attributes. Decisions and identifiers only; no body ever leaves the store."""

from __future__ import annotations

from typing import Any


def attributes_for(trace: dict[str, Any]) -> dict[str, Any]:
    result = trace["result"] or {}
    compressed = {row["item_id"] for row in trace["compressed"]}
    return {
        "cwa.profile": f"{trace['profile']['id']} v{trace['profile']['version']}",
        "cwa.route_policy": trace["context"]["route_policy_version"],
        "cwa.snapshot.digest": trace["context"]["snapshot_digest"],
        "cwa.payload.sha256": result.get("hash", ""),
        "cwa.input_tokens": result.get("input_tokens", 0),
        "cwa.budget.input": trace["budget"]["input"],
        "cwa.refused": trace["refused"]["reason"] or "",
        "cwa.recovery": (trace.get("recovery") or {}).get("action", ""),
        "cwa.included": [row["item_id"] for row in trace["included"] if row["item_id"] not in compressed],
        "cwa.compressed": sorted(compressed),
        "cwa.excluded": [f"{row['item_id']}: {row['reason']}" for row in trace["excluded"]],
        "cwa.conflicts": [f"{g['group_id']}: {g['decided_by']}" + (f", {g['winner']}" if g.get("winner") else "") for g in trace["conflicts"]],
        "cwa.defaults_filled": len(trace["defaults_filled"]),
    }
