"""The committed scenarios: each exercise's snapshot and what the assembler makes of it now.

In each folder under scenarios/, snapshot.json is the exercise's input, built by exercises.py from the vendored example,
and trace.json and payload.json are what the pinned assembler returns. A rejected exercise has rejected.json instead
of a trace. They are committed so a change to the base snapshot, an exercise or the assembler pin shows up as a diff
someone can review, and so a participant can replay any of them without running the exercise code.

    uv run scenarios.py --check    # exit 1 when a committed file differs from what the code builds now
    uv run scenarios.py --write    # rebuild every scenario, then read the diff before committing it

A refused scenario has no payload.json. The trace is stored without trace_id and timings, which may differ run to run
(R-23).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cwa import Snapshot, SnapshotError, assemble

import exercises

SCENARIOS = Path(__file__).parent / "scenarios"


def names() -> list[str]:
    return exercises.names()


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(name: str) -> dict[str, bytes | None]:
    """Every generated file of a scenario, as bytes; None for a file that must not exist."""
    document = exercises.snapshot(name)
    files: dict[str, bytes | None] = {"snapshot.json": _json(document)}
    try:
        result = assemble(Snapshot.from_json(document))
    except SnapshotError as error:
        files.update({"trace.json": None, "payload.json": None,
                      "rejected.json": _json({"rejected": True, "problems": list(error.problems)})})
        return files
    trace = {key: value for key, value in result.trace.items() if key not in ("trace_id", "timings")}
    files.update({"trace.json": _json(trace), "payload.json": result.payload, "rejected.json": None})
    return files


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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        for name in names():
            for line in write(name):
                print(line)
        return 0
    differing = [file for name in names() for file in stale(name)]
    if differing:
        print("stale (run uv run scenarios.py --write, then review the diff):\n  " + "\n  ".join(differing), file=sys.stderr)
        return 1
    print(f"{len(names())} scenarios are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
