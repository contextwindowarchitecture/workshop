"""The committed scenario here is the recorded eval suite: evals/results/scripted-01, one run record per case, graded.

    uv run scenarios.py --check    # rebuild the suite into a temporary directory and compare every run record and the report
    uv run scenarios.py --write    # rebuild evals/results/scripted-01 in place

The records are deterministic: scripted models, a fixed clock, a real MCP server with fixture data. Only the report's
date is excluded from the comparison.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import evals

LABEL = "scripted-01"


def names() -> list[str]:
    return [LABEL]


def _comparable(directory: Path) -> dict[str, object]:
    out: dict[str, object] = {}
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if path.name in ("meta.json", "report.json"):
            doc.pop("date", None)
        out[path.name] = doc
    return out


def stale(name: str) -> list[str]:
    committed = evals.RESULTS / name
    with tempfile.TemporaryDirectory() as tmp:
        original = evals.RESULTS
        evals.RESULTS = Path(tmp)
        try:
            fresh = evals.run_suite(name, False, "solution")
            a, b = _comparable(committed) if committed.exists() else {}, _comparable(fresh)
        finally:
            evals.RESULTS = original
    return [f"{name}/{k}" for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def write(name: str) -> list[str]:
    before = _comparable(evals.RESULTS / name) if (evals.RESULTS / name).exists() else {}
    evals.run_suite(name, False, "solution")
    after = _comparable(evals.RESULTS / name)
    return [f"wrote {name}/{k}" for k in sorted(after) if before.get(k) != after[k]]


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
    print(f"{len(names())} scenario(s) are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
