"""The repair kata: a copy of the reference assembler with defects injected, and the tools to find and fix them.

    python3 kata.py build                 # copy ../assembler-python at its pin into work/, inject the defects, install
    python3 kata.py status                # run the conformance suite in work/ and list what fails, with each case's rules
    python3 kata.py hint <case>           # which stage and module to look in for that case (no line)
    python3 kata.py reveal <case>         # the defect behind that case: file, the wrong line, the right one, and why
    python3 kata.py check                 # the kata is complete: every case passes and every rejection rejects
    python3 kata.py diff                  # your changes against the pristine copy
    python3 kata.py verify-manifest       # (authors) inject each defect alone and record which cases it breaks

work/ and .pristine/ are ignored by git: the kata is rebuilt from the sibling checkout at the pin in shared/contract/pins.json,
so it survives re-vendoring and never duplicates the assembler's source in this repository. Standard library only; uv
does the installing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "shared"))
from siblings import require  # noqa: E402

WORK, PRISTINE = HERE / "work", HERE / ".pristine"
MANIFEST = HERE / "defects" / "manifest.json"
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis", ".idea", ".claude", "node_modules"}
CASES_EXPECTED, REJECTIONS_EXPECTED = 65, 25


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n in SKIP])


def inject(tree: Path, defect: dict) -> None:
    path = tree / defect["file"]
    text = path.read_text(encoding="utf-8")
    if text.count(defect["find"]) != 1:
        raise SystemExit(f"{defect['id']}: expected exactly one occurrence of the target line in {defect['file']}; the assembler at this pin may differ from the manifest")
    path.write_text(text.replace(defect["find"], defect["replace"]), encoding="utf-8")


def source_commit(src: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(src), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def build(args: argparse.Namespace) -> int:
    src = require("assembler-python")
    print(f"copying {src} ({source_commit(src)}) into .pristine/ and work/")
    copy_tree(src, PRISTINE)
    copy_tree(src, WORK)
    for defect in manifest()["defects"]:
        inject(WORK, defect)
    (WORK / "KATA.md").write_text(
        "# This is the kata copy\n\nThe reference assembler at its pinned release, with defects injected by ../kata.py. "
        "Fix it until `python3 ../kata.py check` passes. Work here as the port's AGENTS.md says: a failing test first, "
        "the full suite green before each commit, and `uv run python -m cwa.conformance > conformance-report.json` whenever a case or the code changes.\n",
        encoding="utf-8")
    print(f"injected {len(manifest()['defects'])} defects; installing with uv sync")
    subprocess.run(["uv", "sync", "--quiet"], cwd=WORK, check=True)
    print("built. Next: python3 kata.py status")
    return 0


def conformance(tree: Path) -> dict:
    out = subprocess.run(["uv", "run", "--quiet", "python", "-m", "cwa.conformance"], cwd=tree, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"the conformance runner failed in {tree.name}:\n{out.stderr[-2000:]}")
    (tree / "conformance-report.json").write_text(out.stdout, encoding="utf-8")
    return json.loads(out.stdout)


def failing(report: dict) -> tuple[list[str], list[str]]:
    cases = [c["id"] for c in report["cases"] if c["outcome"] != "passed"]
    rejections = [r["id"] for r in report["rejections"] if r["outcome"] != "rejected"]
    return cases, rejections


def case_meta(tree: Path, case_id: str) -> dict:
    for folder in ("cases", "rejections"):
        path = tree / "conformance" / folder / case_id / "case.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {"rules": [], "description": ""}


def status(args: argparse.Namespace) -> int:
    if not WORK.exists():
        print("no work/ yet: python3 kata.py build", file=sys.stderr)
        return 1
    report = conformance(WORK)
    cases, rejections = failing(report)
    passed = len(report["cases"]) - len(cases)
    print(f"{passed}/{len(report['cases'])} cases pass, {len(report['rejections']) - len(rejections)}/{len(report['rejections'])} rejections reject")
    for case_id in cases:
        meta = case_meta(WORK, case_id)
        print(f"\n  FAIL {case_id}  ({', '.join(meta['rules'])})\n       {meta['description']}")
    for case_id in rejections:
        print(f"\n  NOT REJECTED {case_id}")
    if not cases and not rejections:
        print("\nnothing fails: python3 kata.py check")
    return 0


def _defects_for(case_id: str) -> list[dict]:
    return [defect for defect in manifest()["defects"] if case_id in defect.get("breaks", [])]


def hint(args: argparse.Namespace) -> int:
    defects = _defects_for(args.case)
    if not defects:
        print(f"{args.case} is not broken by an injected defect; if it fails, your fix for something else broke it")
        return 1
    plural = "defects" if len(defects) > 1 else "defect"
    print(f"{args.case} is reached by {len(defects)} injected {plural}:")
    for defect in defects:
        print(f"  the {defect['stage']} stage, in {defect['file']} ({', '.join(defect['rules'])})")
    if len(defects) > 1:
        print("  fixing one is not enough; the case passes only when both are right")
    return 0


def reveal(args: argparse.Namespace) -> int:
    defects = _defects_for(args.case)
    if not defects:
        print(f"{args.case} is not broken by an injected defect")
        return 1
    for defect in defects:
        print(f"{defect['id']}  ({', '.join(defect['rules'])})  {defect['file']}\n\n  wrong:  {defect['replace'].strip()}\n  right:  {defect['find'].strip()}\n\n{defect['why']}\n\nalso breaks: {', '.join(defect['breaks'])}\n")
    return 0


def check(args: argparse.Namespace) -> int:
    report = conformance(WORK)
    cases, rejections = failing(report)
    if cases or rejections:
        print(f"not yet: {len(cases)} case(s) failing, {len(rejections)} rejection(s) not rejected")
        return 1
    print(f"kata complete: {len(report['cases'])}/{CASES_EXPECTED} cases pass and {len(report['rejections'])}/{REJECTIONS_EXPECTED} rejections reject against contract {report['contract']['commit'][:12]}")
    print("now the contributor's finish: uv run pytest in work/ (the report test wants the regenerated report committed), and read status.json")
    return 0


def diff(args: argparse.Namespace) -> int:
    return subprocess.run(["diff", "-ru", "-x", "__pycache__", "-x", ".venv", "-x", "conformance-report.json", "-x", "KATA.md", str(PRISTINE / "src"), str(WORK / "src")]).returncode


def verify_manifest(args: argparse.Namespace) -> int:
    """Inject each defect alone into a scratch copy of the pristine tree and record the cases it breaks."""
    src = require("assembler-python")
    scratch = HERE / ".scratch"
    copy_tree(src, scratch)
    subprocess.run(["uv", "sync", "--quiet"], cwd=scratch, check=True)
    baseline = failing(conformance(scratch))
    if baseline != ([], []):
        print(f"the pristine assembler does not pass: {baseline}", file=sys.stderr)
        return 1
    data = manifest()
    for defect in data["defects"]:
        path = scratch / defect["file"]
        original = path.read_text(encoding="utf-8")
        inject(scratch, defect)
        for cache in scratch.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
        cases, rejections = failing(conformance(scratch))
        path.write_text(original, encoding="utf-8")
        defect["breaks"] = sorted(cases)
        defect["breaks_rejections"] = sorted(rejections)
        print(f"{defect['id']:<32} breaks {len(cases)} case(s): {', '.join(sorted(cases)) or '(none!)'}" + (f"; rejections {rejections}" if rejections else ""))
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.rmtree(scratch, ignore_errors=True)
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("build").set_defaults(func=build)
    sub.add_parser("status").set_defaults(func=status)
    h = sub.add_parser("hint"); h.add_argument("case"); h.set_defaults(func=hint)
    r = sub.add_parser("reveal"); r.add_argument("case"); r.set_defaults(func=reveal)
    sub.add_parser("check").set_defaults(func=check)
    sub.add_parser("diff").set_defaults(func=diff)
    sub.add_parser("verify-manifest").set_defaults(func=verify_manifest)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
