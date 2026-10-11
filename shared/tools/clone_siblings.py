#!/usr/bin/env python3
"""Clone the sibling repositories at the refs shared/contract/pins.json names.

    python3 shared/tools/clone_siblings.py                       # every sibling that is missing
    python3 shared/tools/clone_siblings.py examples website      # just these

A sibling that is already present is left alone and reported with the ref it is at; this script never fetches,
checks out or resets a checkout you already have. The root is the parent of this repository or CWA_SIBLINGS_ROOT.
Standard library only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from siblings import SIBLINGS, pins, root, sibling  # noqa: E402

ORG = "https://github.com/contextwindowarchitecture"


def main(argv: list[str]) -> int:
    names = argv or list(SIBLINGS)
    refs = pins()
    root().mkdir(parents=True, exist_ok=True)
    for name in names:
        path = sibling(name)
        ref = refs.get(name, {}).get("ref", "main")
        if path.is_dir():
            at = subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
            print(f"present  {name:28} at {at or '?'} (pin {ref}); left alone")
            continue
        print(f"clone    {name:28} -> {path} at {ref}")
        subprocess.run(["git", "clone", "--quiet", f"{ORG}/{name}.git", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "checkout", "--quiet", ref], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
