"""The committed scenario is conformance-report.json, produced by the solution adapter through the harness.

    uv run scenarios.py --check    # a fresh report equals the committed one
    uv run scenarios.py --write    # regenerate it
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import harness

REPORT = Path(__file__).parent / "conformance-report.json"


def names() -> list[str]:
    return ["conformance-report"]


def fresh() -> dict:
    return harness.conformance(harness.default_command("solution"), "cwa-assembler", "0.0.1", "python")


def stale(name: str) -> list[str]:
    current = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else None
    return [] if current == fresh() else ["conformance-report.json"]


def write(name: str) -> list[str]:
    REPORT.write_text(json.dumps(fresh(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ["wrote conformance-report.json"]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true"); mode.add_argument("--write", action="store_true")
    args = p.parse_args(argv)
    if args.write:
        print("\n".join(write("conformance-report")))
        return 0
    if stale("conformance-report"):
        print("stale: run uv run scenarios.py --write", file=sys.stderr)
        return 1
    print("1 scenario is current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
