"""Lab B: the specification's own checker, run over a copy of the spec with your case added.

    uv run spec_check.py                 # copy the sibling spec to a scratch directory, add the case, run conformance/check.py
    uv run spec_check.py --keep          # leave the scratch copy for you to open a branch from

This is what CI will do to your pull request. check.py holds every case to the schemas, its digest to the published
definition, a refusal to R-17's shape (no payload file), and the reason codes to the requirements. It also reports the
listed implementations' standing against the corpus as it now is: your case counts as not run by each until it runs it,
which is a warning, not a problem. The sibling checkout is never modified.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from siblings import require  # noqa: E402

CASE = HERE / "cases" / "conflict-tiebreak-not-permitted"
IGNORE = shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__", "assets")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--keep", action="store_true")
    args = p.parse_args(argv)
    spec = require("contextwindowarchitecture")
    scratch = Path(tempfile.mkdtemp(prefix="cwa-spec-"))
    copy = scratch / "contextwindowarchitecture"
    shutil.copytree(spec, copy, ignore=IGNORE)
    target = copy / "conformance" / "cases" / CASE.name
    if target.exists():
        print(f"the spec already has a case named {CASE.name}; pick another id")
        return 1
    shutil.copytree(CASE, target)
    print(f"spec copied to {copy}; case added at conformance/cases/{CASE.name}")
    run = subprocess.run([sys.executable, str(copy / "conformance" / "check.py")], cwd=copy, capture_output=True, text=True)
    sys.stdout.write(run.stdout)
    sys.stderr.write(run.stderr)
    if not args.keep:
        shutil.rmtree(scratch, ignore_errors=True)
    else:
        print(f"kept: {copy}")
    print(f"check.py exit {run.returncode}")
    return run.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
