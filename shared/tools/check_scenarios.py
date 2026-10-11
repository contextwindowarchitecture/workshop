#!/usr/bin/env python3
"""Run every workshop's committed scenario check without a model.

Each workshop directory that has a scenarios.py is a uv project whose `scenarios.py --check` rebuilds its committed
snapshots from their inputs, assembles them, and fails when the payload or trace differs from what is committed. This
runner finds those directories and runs them one after another, so CI and a facilitator have one command:

    python3 shared/tools/check_scenarios.py            # every workshop that has scenarios.py
    python3 shared/tools/check_scenarios.py 02 09/a    # only the directories whose path starts with these

A workshop without scenarios.py is skipped and listed, so a scaffolded module is visible but never fails the build.
Standard library only; uv must be on PATH for the workshops that run.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Participant-facing directories, in catalog order. capstones/ holds one project per domain.
WORKSHOP_GLOBS = ("[0-9][0-9]-*", "[0-9][0-9]-*/[a-z]-*", "capstones/*")


def workshops(prefixes: list[str]) -> list[Path]:
    found: list[Path] = []
    for pattern in WORKSHOP_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if not path.is_dir():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if prefixes and not any(rel.startswith(p) for p in prefixes):
                continue
            found.append(path)
    return found


def main(argv: list[str]) -> int:
    failures = 0
    ran = 0
    for path in workshops(argv):
        rel = path.relative_to(ROOT).as_posix()
        script = path / "scenarios.py"
        if not script.exists():
            print(f"skip   {rel}  (no scenarios.py yet)")
            continue
        print(f"check  {rel}")
        result = subprocess.run(["uv", "run", "--quiet", "scenarios.py", "--check"], cwd=path)
        ran += 1
        if result.returncode != 0:
            failures += 1
            print(f"FAIL   {rel}  (exit {result.returncode})")
    print(f"{ran} checked, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
