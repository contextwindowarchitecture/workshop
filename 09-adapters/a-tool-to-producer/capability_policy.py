"""The capability policy: the only producer that may put a tool in front of the model (R-15). Given, not a lab.

The MCP adapter proposes tool specifications: what the server says it offers. This policy decides which of them the
model is offered for this user's role, with the policy's own description and the server's schema pinned by SHA-256,
so a server that changes a tool loses it until someone reviews the change. Every proposal it declines is reported as
capability_not_allowed at stage producer. The snapshot's grant names the offered ids, so nothing any other producer
emits into governance.capabilities can be admitted.
"""

from __future__ import annotations

import json
from typing import Any

from common import Batch, canonical_sha256, policy


def offer(proposed: list[dict[str, Any]], role: str, now: str) -> tuple[Batch, dict[str, Any]]:
    """The capability-policy batch and the snapshot's grant, for one request."""
    rules = policy("capabilities.json")
    items, excluded = [], []
    for spec in sorted(proposed, key=lambda s: s["name"]):
        cap_id = f"cap:{spec['name']}"
        rule = rules["grants"].get(spec["name"])
        if rule is None or role not in rule["roles"] or rule["schema_sha256"] != canonical_sha256(spec["input_schema"]):
            excluded.append({"item_id": cap_id, "reason": "capability_not_allowed", "stage": "producer"})
            continue
        items.append({
            "id": cap_id, "slot": "governance.capabilities", "source": f"capability-policy:{rules['server']}/{spec['name']}",
            "source_version": rules["allow_list_version"], "authority": "governing", "trust": "verified", "freshness": now,
            "token_budget": None, "variants": [], "conflict_policy": "governs", "lineage": "verbatim",
            "eligibility": "route-policy", "injection_risk": "none",
            "body": json.dumps({"name": spec["name"], "description": rule["description"], "input_schema": spec["input_schema"]}, sort_keys=True),
        })
    grant = {"policy_producer": rules["policy_producer"], "allow_list_version": rules["allow_list_version"],
             "allowed_ids": sorted(i["id"] for i in items)}
    return {"producer": {"id": rules["policy_producer"], "kind": "capability_policy"}, "items": items, "excluded": excluded}, grant
