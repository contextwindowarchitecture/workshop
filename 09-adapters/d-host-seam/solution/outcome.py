"""A refusal mapped to a host outcome. The assembler refusing is not an error the host logs and moves past; it is a
decision the host acts on: no sandbox starts, the run's span carries the reason, and the work item gets a comment that
says what would let a retry succeed (the trace's recovery), in the host's own vocabulary."""

from __future__ import annotations

from typing import Any

RECOVERY = {
    "precompute_summary": "the diff items need precomputed summaries (variants) so fitting can shorten them instead of dropping them",
    "retrieve_narrower": "the producers sent more evidence than fits even as summaries; narrow the diff set or raise the budget",
    "request_context": "no evidence was dropped for budget: the producers or admission left the route without its evidence",
}


def host_outcome(document: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    """What `fullsend run` does with an assembly: start the sandbox with the briefing, or stop before it with a
    comment and span attributes. The comment is written from the trace, never from a model."""
    route = document["route_policy"]["route"]
    if not trace["refused"]["bool"]:
        return {"sandbox": "start", "route": route, "comment": None,
                "span": {"cwa.refused": False, "cwa.snapshot_digest": trace["context"]["snapshot_digest"], "cwa.input_tokens": trace["result"]["input_tokens"]}}
    reason = trace["refused"]["reason"]
    action = (trace.get("recovery") or {}).get("action")
    dropped = [r["item_id"] for r in trace["excluded"] if r["reason"] == "over_budget"]
    comment = (f"fullsend did not start the {route.split('/')[-1]} agent: its briefing was refused ({reason}). "
               + (f"Recovery: {action}, {RECOVERY.get(action, action)}. " if action else "")
               + (f"Left out for budget: {', '.join(dropped)}. " if dropped else "")
               + f"Budget {document['budget']['input']} input tokens under {document['route_policy']['version']}.")
    return {"sandbox": "not started", "route": route, "comment": comment,
            "span": {"cwa.refused": True, "cwa.refused.reason": reason, "cwa.recovery.action": action, "cwa.snapshot_digest": trace["context"]["snapshot_digest"]}}
