"""The committed scenarios: one frozen conversation rendered turn by turn under each candidate profile.

    uv run scenarios.py --check
    uv run scenarios.py --write

scenarios/<profile>/<conversation>-t<n>.{snapshot,trace,payload}.json for every turn, with the solution's profiles.
These are the renders the evaluation suite measures, committed so a change to the item set, the policy, a profile or
the assembler pin shows up as a diff.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app import context
from evaluate import conversations

SCENARIOS = Path(__file__).parent / "scenarios"
CONVERSATION = "export-then-roles"


def names() -> list[str]:
    return sorted(context.profiles("solution"))


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(name: str) -> dict[str, bytes | None]:
    profile = context.profiles("solution")[name]
    files: dict[str, bytes | None] = {}
    for n, request in enumerate(context.turns_of(conversations()[CONVERSATION]), start=1):
        document = context.snapshot(request, profile)
        result = context.assemble(document)
        trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
        stem = f"{CONVERSATION}-t{n}"
        files[f"{stem}.snapshot.json"] = _json(document)
        files[f"{stem}.trace.json"] = _json(trace)
        files[f"{stem}.payload.json"] = result.payload
    return files


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
