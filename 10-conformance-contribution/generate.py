"""Lab A: a new conformance case, written the way the specification's generators write theirs: from a table of intended
outcomes, never from an assembler's output.

    uv run generate.py            # write cases/conflict-tiebreak-not-permitted/{case,snapshot,expected.trace}.json
    uv run generate.py --check    # exit 1 when the committed files differ from what the table implies

The case is the one W8's uncovered defect calls for. A fact group has two leaders from the top-ranked producer with
different freshness, and the route's fact policy does not permit a freshness tie-break. R-11 says the tie-break
decides only when the policy sets one, so the group escalates; the policy says refuse, so assembly refuses with
conflict_unresolved. An assembler that applies the tie-break anyway assembles instead, and this case catches it. The
expected trace below is derived from that sentence, field by field; the only computed value is the snapshot digest,
which is a defined function (RFC 8785 over the normalized snapshot) that the specification's generators publish.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTRACT = ROOT / "shared" / "contract" / "cwa"
CASE = HERE / "cases" / "conflict-tiebreak-not-permitted"
sys.path.insert(0, str(ROOT / "shared"))
from siblings import sibling  # noqa: E402

DEFAULTS = json.loads((CONTRACT / "contract" / "slot-defaults.json").read_text(encoding="utf-8"))
POLICY = ["token_budget", "variants", "conflict_policy", "lineage", "eligibility", "injection_risk"]
T = "2026-09-22T12:00:00Z"
SCOPE = {"tenant": "acme", "user": "u_91", "session": "s_7", "task": "refund_request"}
AUTH = {"governance.instructions": "governing", "evidence.knowledge": "reference_only", "interaction.query": "user"}


def item(id: str, slot: str, body: str, **fields) -> dict:
    """An item with every policy field set, as the spec generators build theirs, so defaults_filled stays empty."""
    d = {"id": id, "slot": slot, "source": "src:" + id, "source_version": "1", "authority": AUTH[slot],
         "trust": "verified" if slot.startswith("governance.") else "unverified", "freshness": "2026-09-22T11:59:00Z", "body": body}
    for f in POLICY:
        d[f] = copy.deepcopy(DEFAULTS[slot][f])
    if slot == "evidence.knowledge":
        d.update(scope={"tenant": "acme"}, freshness="2026-09-12T15:30:00Z", relevance=0.9)
    d.update(fields)
    return d


# --- the table: what this case intends -------------------------------------------------------------------------------

ROUTE = "conflict-tiebreak-not-permitted"
TABLE = {
    "id": ROUTE,
    "rules": ["R-11", "R-17", "R-21"],
    "description": ("Two leaders from the top-ranked producer differ in freshness and the fact policy sets no freshness_tiebreak, so the "
                    "tie is not broken by the clock: the group escalates and the route's on_unresolved refuses with conflict_unresolved. "
                    "An assembler that applies the tie-break without the policy's permission assembles instead."),
    "candidates": [
        ("policy-registry", item("policy:v12", "governance.instructions", "Follow verified refund policy and cite the evidence you use.")),
        ("policy-corpus", item("kb:window-1", "evidence.knowledge", "Refunds are accepted within 14 days of purchase.")),
        ("policy-corpus", item("kb:window-2", "evidence.knowledge", "Refunds are accepted within 30 days of purchase.", freshness="2026-09-13T09:00:00Z")),
        ("conversation", item("turn:18", "interaction.query", "Can I refund my Pro plan?", scope={"session": "s_7"})),
    ],
    "group": {"id": "f-window", "kind": "fact", "fact": "refund.window", "items": ["kb:window-1", "kb:window-2"]},
    "intends": {"decided_by": "escalated", "resolution": "refused", "refusal": "conflict_unresolved"},
}


def snapshot() -> dict:
    batches = {}
    for producer, candidate in TABLE["candidates"]:
        batches.setdefault(producer, []).append(candidate)
    kinds = {"policy-registry": "policy", "policy-corpus": "retrieval", "conversation": "interaction"}
    return {
        "assembly_time": T, "scope": SCOPE, "budget": {"input": 4000, "reserved_output": 1024},
        "profile": {"spec": "cwa/draft", "id": ROUTE, "version": 1, "route": ROUTE, "model_family": None, "route_policy_version": f"{ROUTE}/v1",
                    "placement": [{"slot": "governance.instructions", "wrap": "xml:instructions"}, {"slot": "evidence.knowledge", "wrap": "xml:evidence"}, {"slot": "interaction.query", "wrap": "xml:query"}],
                    "evaluation": {"status": "unevaluated", "suite": None, "date": None, "result": None, "artifact": None}},
        "route_policy": {"route": ROUTE, "version": f"{ROUTE}/v1", "clock_skew_seconds": 5,
                         "producers": {"policy-registry": {"kind": "policy", "slots": ["governance.instructions"]},
                                       "policy-corpus": {"kind": "retrieval", "slots": ["evidence.knowledge"]},
                                       "conversation": {"kind": "interaction", "slots": ["interaction.query"]}},
                         "slots": {"evidence.knowledge": {"min_relevance": 0.5, "required_scope": ["tenant"]}},
                         "facts": {"refund.window": {"precedence": ["policy-corpus"], "scope": ["tenant"], "on_unresolved": "refuse"}}},
        "tokenizer": "fixture-whitespace/v1", "renderer": "fixture-xml/v1",
        "batches": [{"producer": {"id": p, "kind": kinds[p]}, "items": items, "excluded": []} for p, items in batches.items()],
        "conflicts": [TABLE["group"]],
    }


def snapshot_digest(document: dict) -> str:
    """The published digest function from the specification's generators when the sibling is present, else the assembler's."""
    spec = sibling("contextwindowarchitecture")
    generators = spec / "conformance" / "generators"
    if (generators / "digest.py").exists():
        sys.path.insert(0, str(generators))
        import digest  # type: ignore
        return digest.snapshot_digest(document)
    from cwa import Snapshot
    return Snapshot.from_json(document).digest()


def expected_trace(document: dict) -> dict:
    """Derived from the table, field by field, in the order R-21 lists them."""
    g, intends = TABLE["group"], TABLE["intends"]
    return {
        "trace_id": ROUTE,
        "profile": {"id": ROUTE, "version": 1},
        "budget": {"input": 4000, "reserved_output": 1024},
        "result": None,
        "included": [],
        "compressed": [],
        "excluded": [],
        "conflicts": [{"group_id": g["id"], "kind": g["kind"], "items": sorted(g["items"], key=lambda s: s.encode("utf-16-be")),
                       "decided_by": intends["decided_by"], "resolution": intends["resolution"]}],
        "refused": {"bool": True, "reason": intends["refusal"]},
        "context": {"spec": "cwa/draft", "assembly_time": T, "route_policy_version": f"{ROUTE}/v1", "tokenizer": "fixture-whitespace/v1",
                    "renderer": "fixture-xml/v1", "snapshot_digest": snapshot_digest(document)},
        "defaults_filled": [],
    }


def files() -> dict[str, bytes]:
    document = snapshot()
    return {"case.json": _json({"id": TABLE["id"], "rules": TABLE["rules"], "description": TABLE["description"]}),
            "snapshot.json": _json(document), "expected.trace.json": _json(expected_trace(document))}


def _json(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    CASE.mkdir(parents=True, exist_ok=True)
    stale = [name for name, content in files().items() if not (CASE / name).exists() or (CASE / name).read_bytes() != content]
    if args.check:
        print("the case is current" if not stale else f"stale: {stale}")
        return 1 if stale else 0
    for name, content in files().items():
        (CASE / name).write_bytes(content)
    print(f"wrote {CASE.relative_to(HERE)}/: case.json, snapshot.json, expected.trace.json (a refusal: no payload)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
