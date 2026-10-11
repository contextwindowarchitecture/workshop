"""The committed scenario: the triage briefing's snapshot, trace and payload as the solution builds them now.

    uv run scenarios.py --check
    uv run scenarios.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import after

SCENARIOS = Path(__file__).parent / "scenarios"


def names() -> list[str]:
    return ["triage-7811"]


def _json(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(name: str) -> dict[str, bytes | None]:
    document, result = after.build("solution")
    trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
    return {"snapshot.json": _json(document), "trace.json": _json(trace), "payload.json": result.payload}


def stale(name: str) -> list[str]:
    return [f"{name}/{f}" for f, c in build(name).items() if ((SCENARIOS / name / f).read_bytes() if (SCENARIOS / name / f).exists() else None) != c]


def write(name: str) -> list[str]:
    out = []
    for f, c in build(name).items():
        path = SCENARIOS / name / f
        path.parent.mkdir(parents=True, exist_ok=True)
        if c is None:
            if path.exists():
                path.unlink()
                out.append(f"removed {name}/{f}")
        elif not path.exists() or path.read_bytes() != c:
            path.write_bytes(c)
            out.append(f"wrote {name}/{f}")
    return out


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    args = p.parse_args(argv)
    if args.write:
        for n in names():
            for line in write(n):
                print(line)
        return 0
    differing = [f for n in names() for f in stale(n)]
    if differing:
        print("stale (run uv run scenarios.py --write, then review the diff):\n  " + "\n  ".join(differing), file=sys.stderr)
        return 1
    print(f"{len(names())} scenario(s) are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
