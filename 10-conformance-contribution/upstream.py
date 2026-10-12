"""Lab C, last step: stage the case for a pull request against a specification checkout of your own.

    uv run upstream.py --into ../contextwindowarchitecture     # copy the case into that checkout's conformance/cases/ and print what else the PR needs
    uv run upstream.py --into /path/to/your/fork --dry-run      # say what would be written, write nothing
    uv run upstream.py --into ../contextwindowarchitecture --case my-case

It never touches git: you review the diff, run `uv run python conformance/check.py` there, add the CHANGES.md bullet it
prints, move the table into conformance/generators/conflicts.py (the workshop's generate.py is a teaching copy), and
open the pull request yourself. It refuses a target that already has a case of this id, and a target that is not a
specification checkout (no conformance/cases/).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import generate

HERE = Path(__file__).resolve().parent
BULLET = (f"- Conformance corpus: the new {{case}} case holds two leaders at different instants under a fact policy without "
          "`freshness_tiebreak`, which escalates and refuses. An assembler that breaks the tie by the clock without the policy's permission "
          "fails it. Implementations count it as not run until they run it. No requirement changes.")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--into", required=True, help="a checkout of contextwindowarchitecture/contextwindowarchitecture (your fork)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--case", default=generate.DEFAULT_ID, help="the case directory under cases/ to stage")
    args = p.parse_args(argv)
    CASE = HERE / "cases" / args.case
    target = Path(args.into).expanduser().resolve()
    cases = target / "conformance" / "cases"
    if not cases.is_dir():
        print(f"{target} has no conformance/cases/: not a specification checkout")
        return 1
    if args.case == generate.DEFAULT_ID and generate.main(["--check"]) != 0:
        print("the case is stale: run uv run generate.py first")
        return 1
    destination = cases / args.case
    if destination.exists():
        print(f"{destination} already exists; pick another id or remove it first")
        return 1
    files = sorted(p.name for p in CASE.iterdir())
    if args.dry_run:
        print(f"would write {destination}/: {', '.join(files)}")
    else:
        shutil.copytree(CASE, destination)
        print(f"wrote {destination}/: {', '.join(files)}")
    print("\nThen, in that checkout:")
    print("  1. uv run python conformance/check.py                      # the corpus with your case counts and is ok")
    print("  2. move TABLE from this directory's generate.py into conformance/generators/conflicts.py and regenerate: python3 conformance/generators/all.py")
    print("  3. add this bullet under the newest revision in CHANGES.md:\n")
    print("     " + (BULLET.replace("{case}", args.case) if args.case == generate.DEFAULT_ID else f"- Conformance corpus: the new {args.case} case ... (write what it holds, what it expects, what a wrong assembler does; no requirement changes unless one does)"))
    print("\n  4. run every listed assembler against the case and say what each did in the pull request (drafts/case-addition.md)")
    print("  5. git commit -s, and open the pull request from your fork")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
