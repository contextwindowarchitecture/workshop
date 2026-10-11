"""The committed scenarios: each conversation's attempts, with the solution's review list and routes table.

Each folder holds conversation.json plus, per attempt, <n>-<route>.snapshot.json, .trace.json and, unless refused,
.payload.json. A scenario may set "budget" to override budget.input on the first attempt, "route" to start somewhere
other than the default, and "review": "labs" to use the unreviewed list, which is how 05-unreviewed shows an
unfaithful summary reaching the payload.

    uv run scenarios.py --check
    uv run scenarios.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app import app
from request import Request

SCENARIOS = Path(__file__).parent / "scenarios"
SETTINGS = {
    "02-export-squeezed": {"budget": 560},
    "04-recovery": {"budget": 400},
    "05-unreviewed": {"review": "labs", "budget": 500},
}


def names() -> list[str]:
    return sorted(p.parent.name for p in SCENARIOS.glob("*/conversation.json"))


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(name: str) -> dict[str, bytes | None]:
    settings = SETTINGS.get(name, {})
    request = Request.load(SCENARIOS / name / "conversation.json")
    which = settings.get("review", "solution")
    files: dict[str, bytes | None] = {}
    for n, (route, document, result) in enumerate(app.attempts(request, settings.get("route"), which, settings.get("budget")), start=1):
        trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
        files[f"{n}-{route}.snapshot.json"] = _json(document)
        files[f"{n}-{route}.trace.json"] = _json(trace)
        files[f"{n}-{route}.payload.json"] = result.payload
    return files


def stale(name: str) -> list[str]:
    built = build(name)
    found: list[str] = []
    for file, content in built.items():
        path = SCENARIOS / name / file
        if (path.read_bytes() if path.exists() else None) != content:
            found.append(f"{name}/{file}")
    for path in (SCENARIOS / name).glob("*.json"):
        if path.name != "conversation.json" and path.name not in built:
            found.append(f"{name}/{path.name} (left over)")
    return found


def write(name: str) -> list[str]:
    written = []
    built = build(name)
    for path in (SCENARIOS / name).glob("*.json"):
        if path.name != "conversation.json" and path.name not in built:
            path.unlink()
            written.append(f"removed {name}/{path.name}")
    for file, content in built.items():
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
