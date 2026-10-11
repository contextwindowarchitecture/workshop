"""The capability policy producer: the only producer of governance.capabilities (R-15). From W5, with its policy file fixed.

offer() takes what the server proposes and grants what the chosen policy file allows for the user's role, with the
policy's own description and the server's schema pinned by hash; every other proposal is reported as
capability_not_allowed at stage producer. On the final turn nothing is offered, so the model must answer. The
snapshot's grant names the offered ids, so nothing any other producer emits into the slot is admitted.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

POLICY_FILE = __import__('pathlib').Path(__file__).resolve().parent / 'policy' / 'capabilities.json'


@dataclass(frozen=True)
class Grant:
    tool: str
    cap_id: str
    input_schema: dict[str, Any]
    scope: dict[str, str]  # argument -> the request scope key it must equal


def schema_sha256(schema: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def policy(which: str | None = None) -> dict[str, Any]:
    return json.loads(POLICY_FILE.read_text(encoding="utf-8"))


def offer(proposed: list[dict[str, Any]], role: str, now: str, *, final_turn: bool = False, which: str | None = None
          ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Grant]]:
    rules = policy(which)
    items, excluded, granted = [], [], {}
    for spec in [] if final_turn else sorted(proposed, key=lambda s: s["name"]):
        cap_id = f"cap:{spec['name']}"
        rule = rules["grants"].get(spec["name"])
        if rule is None or role not in rule["roles"] or rule.get("schema_sha256") != schema_sha256(spec["input_schema"]):
            excluded.append({"item_id": cap_id, "reason": "capability_not_allowed", "stage": "producer"})
            continue
        granted[spec["name"]] = Grant(spec["name"], cap_id, spec["input_schema"], rule.get("scope", {}))
        items.append({
            "id": cap_id, "slot": "governance.capabilities", "source": f"capability-policy:{rules['server']}/{spec['name']}",
            "source_version": rules["allow_list_version"], "authority": "governing", "trust": "verified", "freshness": now,
            "token_budget": None, "variants": [], "conflict_policy": "governs", "lineage": "verbatim",
            "eligibility": "route-policy", "injection_risk": "none",
            "body": json.dumps({"name": spec["name"], "description": rule["description"], "input_schema": spec["input_schema"]}, sort_keys=True),
        })
    batch = {"producer": {"id": rules["policy_producer"], "kind": "capability_policy"}, "items": items, "excluded": excluded}
    grant = {"policy_producer": rules["policy_producer"], "allow_list_version": rules["allow_list_version"],
             "allowed_ids": sorted(i["id"] for i in items)}
    return batch, grant, granted
