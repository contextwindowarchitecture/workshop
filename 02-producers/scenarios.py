"""The committed scenarios: what the solution producers propose for each request, and what the assembler decides.

Each folder under scenarios/ holds request.json (the input), snapshot.json (the frozen batches with the route's
policy), trace.json and, unless refused, payload.json. The neg-* scenarios add one of Lab D's wrong items to the
first request and commit the code it earns. They are committed so a change to the data, a producer, the policy or the
assembler pin shows up as a diff someone can review, and so the labs have an answer key that is not prose.

    uv run scenarios.py --check    # exit 1 when a committed file differs from what the code builds now
    uv run scenarios.py --write    # rebuild every scenario, then read the diff before committing it
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cwa import Snapshot, assemble

import common
import freeze
from solution import negative

SCENARIOS = Path(__file__).parent / "scenarios"

REQUESTS: dict[str, dict[str, Any]] = {
    "01-ada-export": {"user": "u_ada", "question": "How do I export the whole workspace, including attachments?", "history": True},
    "02-cho-refund": {"user": "u_cho", "question": "Can I get a refund on a monthly plan?"},
    "03-memory-leak": {"user": "u_ben", "question": "Which plan are we on?", "faults": ["memory-store-ignores-user"]},
    "04-stale-account-read": {"user": "u_ada", "question": "Who can change our billing details?", "read_at": "2026-10-01T09:50:00Z"},
    "05-budget-variants": {"user": "u_ada", "question": "How do I export the whole workspace, including attachments?", "history": True, "budget": 600},
}
for name in negative.EXPECTED:
    REQUESTS[f"neg-{name.replace('_', '-')}"] = {**REQUESTS["01-ada-export"], "negative": name}


def names() -> list[str]:
    return sorted(REQUESTS)


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def document(name: str) -> dict[str, Any]:
    spec = REQUESTS[name]
    req = freeze.request(spec["user"], spec["question"], read_at=spec.get("read_at"),
                         faults=tuple(spec.get("faults", [])), history=spec.get("history", False))
    batches = freeze.batches(req, "solution")
    if "negative" in spec:
        bad = getattr(negative, spec["negative"])()
        next(b for b in batches if b["producer"]["id"] == "help-center-search")["items"].append(bad)
    doc = common.snapshot(req, batches)
    if "budget" in spec:
        doc["budget"]["input"] = spec["budget"]
    return doc


def build(name: str) -> dict[str, bytes | None]:
    doc = document(name)
    result = assemble(Snapshot.from_json(doc))
    trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
    return {"request.json": _json(REQUESTS[name]), "snapshot.json": _json(doc), "trace.json": _json(trace),
            "payload.json": result.payload}


def stale(name: str) -> list[str]:
    found = []
    for file, content in build(name).items():
        path = SCENARIOS / name / file
        current = path.read_bytes() if path.exists() else None
        if current != content:
            found.append(f"{name}/{file}")
    return found


def write(name: str) -> list[str]:
    written = []
    (SCENARIOS / name).mkdir(parents=True, exist_ok=True)
    for file, content in build(name).items():
        path = SCENARIOS / name / file
        if content is None:
            if path.exists():
                path.unlink()
                written.append(f"removed {name}/{file}")
        elif not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)
            written.append(f"wrote {name}/{file}")
    return written


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = p.parse_args(argv)
    if args.write:
        for name in names():
            for line in write(name):
                print(line)
        return 0
    differing = [f for name in names() for f in stale(name)]
    if differing:
        print("stale (run uv run scenarios.py --write, then review the diff):\n  " + "\n  ".join(differing), file=sys.stderr)
        return 1
    print(f"{len(names())} scenarios are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
