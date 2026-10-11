"""The committed scenarios: each request's frozen snapshot and what the assembler decides, built with the solution.

    uv run scenarios.py --check    # exit 1 when a committed file differs from what the code builds now
    uv run scenarios.py --write    # rebuild every scenario, then read the diff before committing it

Each folder holds request.json, snapshot.json, trace.json and, unless refused, payload.json. The MCP server runs for
real on every build; its answers are deterministic, and the observed_at of each call comes from the script, so the
snapshots are byte-stable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cwa import Snapshot, assemble

import run

SCENARIOS = Path(__file__).parent / "scenarios"
Q = "How do I export the whole workspace, including attachments?"
REQUESTS: dict[str, dict[str, Any]] = {
    "01-retriever": {"user": "u_ada", "question": Q, "calls": []},
    "02-memory-reported": {"user": "u_ada", "question": "Which identity provider do we use?", "calls": []},
    "03-memory-silent-fault": {"user": "u_ada", "question": "Which identity provider do we use?", "calls": [], "faults": ["silent-sql"]},
    "04-observations-superseded": {"user": "u_ada", "question": "Is there an incident in our region right now?", "calls": ["account", "status", "status"]},
    "05-specs-as-items-fault": {"user": "u_ada", "question": "What plan are we on?", "calls": ["account"], "faults": ["specs-as-items"]},
    "06-member-not-granted": {"user": "u_ben", "question": "Who are the billing admins?", "calls": ["account"]},
}


def names() -> list[str]:
    return sorted(REQUESTS)


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def document(name: str) -> dict[str, Any]:
    spec = REQUESTS[name]
    req = run.request(spec["user"], spec["question"])
    return run.build(req, run.scripted_calls(spec["user"], spec["calls"]), "solution", tuple(spec.get("faults", [])))


def build(name: str) -> dict[str, bytes | None]:
    doc = document(name)
    result = assemble(Snapshot.from_json(doc))
    trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
    return {"request.json": _json(REQUESTS[name]), "snapshot.json": _json(doc), "trace.json": _json(trace), "payload.json": result.payload}


def stale(name: str) -> list[str]:
    found = []
    for file, content in build(name).items():
        path = SCENARIOS / name / file
        if (path.read_bytes() if path.exists() else None) != content:
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
