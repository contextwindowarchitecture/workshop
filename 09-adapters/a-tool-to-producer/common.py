"""What every adapter lab shares: the request, item and batch helpers, the policy, the freeze and the decisions table.

The lesson is in labs/: turning what a tool already returns into a conformant producer batch, without changing the
tool. This module is the surrounding application: it authenticates the user, binds the scope, freezes what the
adapters proposed with the route's policy, and hands the snapshot to the reference assembler unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from cwa import AssemblyResult, Snapshot, assemble

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = ROOT / "shared" / "contract" / "cwa"
POLICY = HERE / "policy"
sys.path.insert(0, str(ROOT / "shared"))
from fernway import ACCOUNTS, MEMORIES  # noqa: E402,F401
from fernway.corpus import jaccard, words  # noqa: E402,F401

Item = dict[str, Any]
Batch = dict[str, Any]


@dataclass(frozen=True)
class Request:
    """One question from one signed-in user, with the clock read once. The application authenticated the user and
    bound tenant, user and session before any tool ran."""

    tenant: str
    user: str
    role: str
    session: str
    asked_at: str
    question: str

    @property
    def scope(self) -> dict[str, str]:
        return {"tenant": self.tenant, "user": self.user, "session": self.session}


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def item(**fields: Any) -> Item:
    """A context item with its policy fields declared, so defaults_filled stays short (R-3)."""
    return {"token_budget": None, "variants": [], "conflict_policy": "defers", "eligibility": "route-policy", **fields}


def batch(producer_id: str, kind: str, items: list[Item], excluded: list[dict[str, Any]] | None = None) -> Batch:
    return {"producer": {"id": producer_id, "kind": kind}, "items": items, "excluded": excluded or []}


def canonical_sha256(value: Any) -> str:
    """SHA-256 of a value's canonical JSON: how the capability policy pins a tool's input schema."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def policy(name: str) -> Any:
    return json.loads((POLICY / name).read_text(encoding="utf-8"))


def contract(relative: str) -> Any:
    return json.loads((CONTRACT / relative).read_text(encoding="utf-8"))


def snapshot(request: Request, batches: list[Batch], grant: dict[str, Any] | None = None) -> dict[str, Any]:
    """Freeze the batches with the route's policy, the profile, the budget, the clock and, when tools are offered,
    the capability grant (snapshot.schema.json). Done once per call, after every producer has run (R-23)."""
    settings = policy("assembly.json")
    document = {
        "assembly_time": request.asked_at,
        "scope": request.scope,
        "budget": settings["budget"],
        "profile": policy("profile.json"),
        "route_policy": policy("route-policy.json"),
        "tokenizer": settings["tokenizer"],
        "renderer": settings["renderer"],
        "batches": batches,
        "conflicts": [],
    }
    if grant is not None:
        document["capabilities"] = grant
    return document


def freeze_and_assemble(request: Request, batches: list[Batch], grant: dict[str, Any] | None = None) -> tuple[dict[str, Any], AssemblyResult]:
    document = snapshot(request, batches, grant)
    return document, assemble(Snapshot.from_json(document))


def report(document: dict[str, Any], result: AssemblyResult, out: TextIO = sys.stdout, defaults: bool = False) -> None:
    """The trace as a table: + included, ~ compressed, - excluded with reason and stage, ! conflicts."""
    trace = result.trace
    candidates = {i["id"]: i for b in document["batches"] for i in b["items"]}
    if trace["refused"]["bool"]:
        recovery = (trace.get("recovery") or {}).get("action")
        print(f"REFUSED: {trace['refused']['reason']}" + (f"  recovery: {recovery}" if recovery else ""), file=out)
    else:
        budget = trace["budget"]
        print(f"assembled {trace['profile']['id']} v{trace['profile']['version']}: {trace['result']['input_tokens']} "
              f"input tokens of {budget['input']} with a {budget.get('margin_percent', 0)}% margin, "
              f"payload sha256 {trace['result']['hash'][:16]}", file=out)
    for row in trace["included"]:
        rel = candidates.get(row["item_id"], {}).get("relevance")
        print(f"  + {row['slot']:<24} {row['item_id']:<36} {row['tokens']:>4} tokens"
              + (f"  relevance {rel:g}" if rel is not None else ""), file=out)
    for row in trace["compressed"]:
        print(f"  ~ {row['slot']:<24} {row['item_id']:<36} {row['from']:>4} -> {row['to']} tokens  variant {row['variant_id']}", file=out)
    for row in trace["excluded"]:
        slot = row.get("slot") or candidates.get(row["item_id"], {}).get("slot", "")
        extra = f"  duplicate_of {row['duplicate_of']}" if row.get("duplicate_of") else ""
        extra += f"  superseded_by {row['superseded_by']}" if row.get("superseded_by") else ""
        print(f"  - {slot:<24} {row['item_id']:<36} {row['reason']}  [{row['stage']}]{extra}", file=out)
    for row in trace["conflicts"]:
        print(f"  ! {row['kind']:<24} {row['group_id']:<36} {row['resolution']} by {row['decided_by']}", file=out)
    filled = trace["defaults_filled"]
    print(f"  defaults filled: {len(filled)}   snapshot digest {trace['context']['snapshot_digest'][:16]}", file=out)
    if defaults and filled:
        by_item: dict[str, list[str]] = {}
        for row in filled:
            by_item.setdefault(row["item_id"], []).append(row["field"])
        for item_id, fields in by_item.items():
            print(f"      {item_id:<36} {', '.join(fields)}", file=out)
