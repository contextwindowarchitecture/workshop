"""The committed scenarios: each conversation's snapshot, trace and payload as the solution builds them now.

    uv run scenarios.py --check    # exit 1 when a committed file differs from what the code builds now
    uv run scenarios.py --write    # rebuild every scenario, then read the diff before committing it

conversation.json is the input; snapshot.json, trace.json and, unless refused, payload.json are what the migrated
application builds from it. A change to an article, a memory, the policy or the assembler pin shows up here as a diff.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from request import Request
from solution import context

SCENARIOS = Path(__file__).parent / "scenarios"


def names() -> list[str]:
    return sorted(p.parent.name for p in SCENARIOS.glob("*/conversation.json"))


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(name: str) -> dict[str, bytes | None]:
    document = context.snapshot(Request.load(SCENARIOS / name / "conversation.json"))
    result = context.assemble(document)
    trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
    return {"snapshot.json": _json(document), "trace.json": _json(trace), "payload.json": result.payload}


def stale(name: str) -> list[str]:
    found = []
    for file, content in build(name).items():
        path = SCENARIOS / name / file
        if (path.read_bytes() if path.exists() else None) != content:
            found.append(f"{name}/{file}")
    return found


def write(name: str) -> list[str]:
    written = []
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
