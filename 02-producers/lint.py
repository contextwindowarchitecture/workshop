"""Local checks on producer batches, in the assembler's own vocabulary. Passing them is not admission.

    uv run lint.py                      # lint the solution producers' batches for a sample request
    uv run lint.py --impl labs          # lint yours
    uv run lint.py --impl labs --json   # machine-readable
    uv run lint.py --negatives          # Lab D's wrong items too: see which the linter catches and which only the trace does

Each finding names the item, the reason code the assembler would most likely record, and the requirement. The checks
are the ones a producer can run on its own output before any snapshot exists: schema shape (with date-time formats
asserted), the slot-specific required fields, the kind-to-slot gate, authority per slot, the injection marker, tier
claims, variant ids, scope keys and source prefix from the route, and the shape of each excluded row. What they cannot
check is anything that depends on the rest of the snapshot or on the clock: authentication, duplicate ids across
producers, expiry, staleness, relevance thresholds, conflicts, budget. For those, freeze and read the trace.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

import common
import freeze
import impl

ITEM_SCHEMA = common.contract("schema/context_item.schema.json")
REASONS = common.contract("contract/reasons.json")
SLOT_DEFAULTS = common.contract("contract/slot-defaults.json")
EXCLUSION_CODES = {r["code"] for r in REASONS if r["kind"] == "exclusion"}
TIERS = {"droppable": 0, "compressible": 1, "protected": 2}
# R-1: the authority each slot takes, and the slots where untrusted may stand in.
UNTRUSTED_OK = {"evidence.tool_results", "interaction.memory", "interaction.history"}
# R-13, R-14, R-15, R-8: the slots a producer kind may address at all, whatever the route lists.
KIND_SLOTS = {
    "retrieval": {"evidence.knowledge", "evidence.tool_results"},
    "memory": {"interaction.memory"},
    "state": {"state.user", "state.task"},
    "mcp": {"evidence.knowledge", "evidence.tool_results", "governance.capabilities"},
    "capability_policy": {"governance.capabilities"},
}
_validator = Draft202012Validator(ITEM_SCHEMA, format_checker=FormatChecker())


def lint_batch(batch: dict[str, Any], route: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    producer = batch["producer"]
    listed = route["producers"].get(producer["id"])
    if listed is None:
        findings.append(_f("(batch)", "producer_not_authenticated", "R-15", f"{producer['id']} is not listed by the route"))
    elif listed["kind"] != producer["kind"]:
        findings.append(_f("(batch)", "producer_not_authenticated", "R-15", f"route lists {producer['id']} as {listed['kind']}, batch says {producer['kind']}"))
    ids = [i.get("id") for i in batch["items"]]
    for item in batch["items"]:
        findings.extend(lint_item(item, producer, listed, route))
        if ids.count(item.get("id")) > 1:
            findings.append(_f(item.get("id"), "duplicate_item_id", "R-2", "id reused within the batch"))
    candidate_ids = set(ids)
    for row in batch.get("excluded", []):
        where = row.get("item_id", "(excluded row)")
        reason = row.get("reason", "")
        if reason not in EXCLUSION_CODES and not reason.startswith("missing_field:"):
            findings.append(_f(where, "(snapshot rejected)", "R-9", f"excluded reason {reason!r} is not an exclusion code"))
        if row.get("stage") != "producer":
            findings.append(_f(where, "(snapshot rejected)", "R-9", "excluded row must have stage: producer"))
        for key, needs in (("duplicate_of", "duplicate_content"), ("superseded_by", "superseded")):
            if reason == needs and row.get(key) not in candidate_ids:
                findings.append(_f(where, "(snapshot rejected)", "R-13", f"{key} must name a candidate in this batch"))
            if reason != needs and key in row:
                findings.append(_f(where, "(snapshot rejected)", "R-9", f"{key} only belongs on a {needs} row"))
        if where in candidate_ids:
            findings.append(_f(where, "duplicate_item_id", "R-2", "an excluded id is also a candidate id"))
    return findings


def lint_item(item: dict[str, Any], producer: dict[str, str], listed: dict[str, Any] | None, route: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    where = item.get("id") or "(no id)"
    for error in sorted(_validator.iter_errors(item), key=lambda e: list(e.path)):
        if error.validator == "required":
            missing = error.message.split("'")[1]
            out.append(_f(where, f"missing_field:{missing}", "R-2", "required field absent"))
        else:
            path = ".".join(str(p) for p in error.path) or "(item)"
            out.append(_f(where, "invalid_structure", "R-2", f"{path}: {error.message[:90]}"))
    slot = item.get("slot")
    if slot not in SLOT_DEFAULTS:
        return out  # unknown_slot is already a schema error above
    defaults = SLOT_DEFAULTS[slot]
    kind = producer["kind"]
    if kind in KIND_SLOTS and slot not in KIND_SLOTS[kind]:
        out.append(_f(where, "producer_slot_not_allowed", "R-13", f"a {kind} producer may not address {slot}"))
    elif listed and slot not in listed["slots"]:
        out.append(_f(where, "producer_slot_not_allowed", "R-15", f"the route does not list {slot} for {producer['id']}"))
    authority = item.get("authority")
    if authority is not None and authority != defaults["authority"] and not (authority == "untrusted" and slot in UNTRUSTED_OK):
        out.append(_f(where, "authority_not_allowed", "R-1", f"{slot} takes {defaults['authority']}, not {authority}"))
    if slot.startswith("governance.") and (item.get("trust") != "verified" or item.get("injection_risk", defaults["injection_risk"]) != "none"):
        out.append(_f(where, "untrusted_in_governance", "R-10", "governance items must be verified and unmarked"))
    if defaults["injection_risk"] == "untrusted_content" and item.get("injection_risk", "untrusted_content") != "untrusted_content":
        out.append(_f(where, "untrusted_content_unmarked", "R-10", f"{slot} content must carry injection_risk: untrusted_content"))
    tier = item.get("tier")
    if tier is not None:
        if TIERS[tier] > TIERS[defaults["tier"]]:
            out.append(_f(where, "tier_upgrade_not_allowed", "R-16", f"{slot} is {defaults['tier']} by default; only the route raises it"))
        elif defaults["tier"] == "protected" and tier != "protected":
            out.append(_f(where, "protected_tier_changed", "R-16", "an item cannot lower a protected slot's tier"))
    variant_ids = [v.get("id") for v in item.get("variants", [])]
    if len(set(variant_ids)) != len(variant_ids) or item.get("id") in variant_ids:
        out.append(_f(where, "duplicate_variant_id", "R-18", "variant ids must be unique and differ from the item's"))
    if slot == "evidence.knowledge" and "relevance" not in item:
        out.append(_f(where, "missing_field:relevance", "R-13", "every evidence.knowledge item carries its rerank score"))
    if slot == "interaction.memory" and "expires" not in item:
        out.append(_f(where, "missing_field:expires", "R-9", "every memory item carries an expires deadline"))
    rules = route.get("slots", {}).get(slot, {})
    for key in rules.get("required_scope", []):
        if key not in item.get("scope", {}):
            out.append(_f(where, "out_of_scope", "R-2", f"the route requires scope.{key} in {slot}; a missing key is never a wildcard"))
    prefix = rules.get("source_prefix")
    if prefix and not str(item.get("source", "")).startswith(prefix):
        out.append(_f(where, "source_invalid", "R-3", f"source must start with {prefix!r} in {slot}"))
    seen: set[tuple[str, str]] = set()
    return [f for f in out if (f["item"], f["code"]) not in seen and not seen.add((f["item"], f["code"]))]


def _f(item: str, code: str, rule: str, note: str) -> dict[str, str]:
    return {"item": str(item), "code": code, "rule": rule, "note": note}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    p.add_argument("--user", choices=sorted(freeze.TENANT), default="u_ada")
    p.add_argument("--question", default="How do I export the whole workspace, including attachments?")
    p.add_argument("--json", action="store_true")
    p.add_argument("--negatives", action="store_true", help="also lint Lab D's five wrong items, appended to the search batch")
    args = p.parse_args(argv)
    route = common.policy("route-policy.json")
    req = freeze.request(args.user, args.question, history=True)
    all_findings: dict[str, list[dict[str, str]]] = {}
    try:
        batches = freeze.batches(req, args.impl)
        if args.negatives:
            negative = impl.module("negative", args.impl)
            search = next(b for b in batches if b["producer"]["id"] == "help-center-search")
            search["items"].extend(getattr(negative, name)() for name in negative.EXPECTED)
    except NotImplementedError as todo:
        print(f"a lab producer is not written yet: {todo}")
        return 2
    for batch in batches:
        all_findings[batch["producer"]["id"]] = lint_batch(batch, route)
    if args.json:
        print(json.dumps(all_findings, indent=2))
    else:
        total = 0
        for producer, findings in all_findings.items():
            print(f"{producer}: {'clean' if not findings else str(len(findings)) + ' finding(s)'}")
            for f in findings:
                print(f"  {f['item']:<34} {f['code']:<28} {f['rule']:<5} {f['note']}")
            total += len(findings)
        print(f"\n{total} finding(s). Local checks only: passing is not admission. Freeze and read the trace:"
              f"\n  uv run freeze.py --impl {impl.name(args.impl)} --user {args.user} --defaults {args.question!r}")
    return 1 if any(all_findings.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
