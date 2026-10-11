"""The invariants, run over every snapshot this repository has committed: the model-free half of any CWA benchmark.

    uv run invariants.py            # every workshop's committed snapshots: replays, schema, recorded hashes
    uv run invariants.py --json     # the same as a document

The examples bench separates two kinds of result. Invariants hold for every model, and a failure is a bug in the
application or the assembler: the request sent equals the payload, a refusal sends nothing, every snapshot replays to
the same bytes, and the same question gives every model the same snapshot. Construct measures say how a model used the
context it was given, and vary by model. This script runs the invariants a repository can check without a model over
the snapshots W1 to W7, W9 and the capstone committed: a replay of each (R-23), its trace against the published schema
(R-21), and, where a trace or payload was committed beside it, the recorded hash against the fresh one.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from cwa import Snapshot, SnapshotError, assemble
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCHEMA = json.loads((ROOT / "shared" / "contract" / "cwa" / "schema" / "trace.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
SKIP_PARTS = {".venv", "node_modules", "__pycache__", "work", ".pristine", "shared"}


def looks_like_snapshot(doc) -> bool:
    return isinstance(doc, dict) and "batches" in doc and "route_policy" in doc and "profile" in doc


def snapshots():
    """(workshop, label, snapshot, recorded trace or None) for every committed snapshot, wherever its file keeps it."""
    for path in sorted(ROOT.rglob("*.json")):
        if any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts) or path.relative_to(ROOT).parts[0] in ("docs", ".github"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        workshop = path.relative_to(ROOT).parts[0]
        if looks_like_snapshot(doc):
            stem = path.name[: -len(".snapshot.json")] if path.name.endswith(".snapshot.json") else None
            trace_path = path.with_name(f"{stem}.trace.json") if stem else path.with_name("trace.json")
            rejected_path = path.with_name(f"{stem}.rejected.json") if stem else path.with_name("rejected.json")
            trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.exists() else None
            if rejected_path.exists():
                trace = json.loads(rejected_path.read_text(encoding="utf-8"))
            yield workshop, str(path.relative_to(ROOT)), doc, trace
        elif isinstance(doc, dict):
            for key in ("inferences", "attempts"):
                for n, entry in enumerate(doc.get(key) or []):
                    if isinstance(entry, dict) and looks_like_snapshot(entry.get("snapshot")):
                        yield workshop, f"{path.relative_to(ROOT)}#{key}[{n}]", entry["snapshot"], entry.get("trace")


def check(doc: dict, recorded: dict | None) -> dict:
    """A snapshot committed with a rejected.json is expected to be rejected, with the recorded problems (R-5 is an invariant too)."""
    out = {"replays": False, "schema": False, "recorded": None, "problem": None}
    expects_rejection = isinstance(recorded, dict) and recorded.get("rejected") is True
    try:
        first, second = assemble(Snapshot.from_json(doc)), assemble(Snapshot.from_json(doc))
    except SnapshotError as error:
        if expects_rejection:
            out.update(replays=True, schema=True, recorded=list(error.problems) == recorded["problems"])
        else:
            out["problem"] = f"rejected: {error.problems[:1]}"
        return out
    if expects_rejection:
        out["problem"] = "assembled, but rejected.json says the snapshot is rejected"
        return out
    strip = lambda t: {k: v for k, v in t.items() if k not in ("trace_id", "timings")}
    out["replays"] = first.payload == second.payload and strip(first.trace) == strip(second.trace)
    out["schema"] = not list(VALIDATOR.iter_errors(first.trace))
    if recorded is not None:
        out["recorded"] = strip(first.trace) == strip(recorded)
    return out


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    rows, per = [], {}
    for workshop, label, doc, recorded in snapshots():
        result = check(doc, recorded)
        rows.append({"workshop": workshop, "snapshot": label, **result})
        counts = per.setdefault(workshop, Counter())
        counts["snapshots"] += 1
        counts["replays"] += result["replays"]
        counts["schema"] += result["schema"]
        counts["recorded_checked"] += result["recorded"] is not None
        counts["recorded_match"] += bool(result["recorded"])
        counts["problems"] += result["problem"] is not None
    if args.json:
        print(json.dumps({"per_workshop": per, "snapshots": rows}, indent=2))
        return 0
    print(f"{'workshop':<36}{'snapshots':>10}{'replay':>8}{'schema':>8}{'recorded':>10}{'problems':>10}")
    for workshop, c in per.items():
        print(f"{workshop:<36}{c['snapshots']:>10}{c['replays']:>8}{c['schema']:>8}{str(c['recorded_match']) + '/' + str(c['recorded_checked']):>10}{c['problems']:>10}")
    failures = [r for r in rows if not r["replays"] or not r["schema"] or r["recorded"] is False or r["problem"]]
    for r in failures:
        print(f"  FAIL {r['snapshot']}: {r}")
    total = sum(c["snapshots"] for c in per.values())
    print(f"\n{total} snapshots; {len(failures)} invariant failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
