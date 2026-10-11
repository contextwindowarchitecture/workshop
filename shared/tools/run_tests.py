#!/usr/bin/env python3
"""Run every module's test suite in its own uv environment, and optionally prove that every module's stubs fail.

    python3 shared/tools/run_tests.py             # every module that has tests/: uv run pytest, solution mode
    python3 shared/tools/run_tests.py --labs      # the same with each module's stub implementation selected: the suite must FAIL
    python3 shared/tools/run_tests.py 05 09/a     # only the modules whose path starts with these

A module is a directory with a pyproject.toml and a tests/ folder. Its implementation switch, when it has one, is the
CWA_<MODULE>_IMPL variable its impl.py (or seam_impl.py) reads; the stub choice is the one that is not "solution".
In --labs mode a module whose stubs pass its own gate is reported as a problem: the gate would not be checking anything.
Siblings are found as the modules find them (CWA_SIBLINGS_ROOT and CWA_SIBLING_<NAME> pass through). Standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".venv", "node_modules", "__pycache__", "work", ".pristine", "shared", ".git", ".scratch"}
ENV_NAME = re.compile(r'os\.environ\.get\("(CWA_\w+_IMPL)"')
CHOICES = re.compile(r'not in \(((?:"\w+",?\s*)+)\)')


def modules(prefixes: list[str]) -> list[Path]:
    out = []
    for tests in sorted(ROOT.rglob("tests")):
        rel = tests.relative_to(ROOT)
        if not tests.is_dir() or any(part in SKIP_PARTS for part in rel.parts) or not (tests.parent / "pyproject.toml").exists():
            continue
        if prefixes and not any(str(rel.parent).startswith(p) for p in prefixes):
            continue
        out.append(tests.parent)
    return out


def stub_switch(module: Path) -> tuple[str, str] | None:
    """(environment variable, stub value) for a module with an implementation switch, else None. The switch is read
    from whichever top-level module names it; the stub value is the choice that is not "solution", or the lab
    directory's name when the module lists no choices."""
    for path in sorted(module.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        env = ENV_NAME.search(text)
        if not env:
            continue
        choices = CHOICES.search(text)
        if choices:
            stubs = [v for v in re.findall(r'"(\w+)"', choices.group(1)) if v != "solution"]
            if stubs:
                return env.group(1), stubs[0]
        for folder in ("labs", "skeleton", "after"):
            if (module / folder).is_dir():
                return env.group(1), folder
    return None


def run(module: Path, labs: bool) -> tuple[str, str, float]:
    """(status, last line, seconds). status: ok, FAIL, skip, or for --labs: stubs-fail, STUBS-PASS."""
    env = dict(os.environ)
    switch = stub_switch(module)
    if labs:
        if switch is None:
            return "skip", "no implementation switch", 0.0
        env[switch[0]] = switch[1]
    started = time.monotonic()
    proc = subprocess.run(["uv", "run", "--quiet", "pytest", "-q", "-p", "no:cacheprovider"], cwd=module, env=env, capture_output=True, text=True)
    seconds = time.monotonic() - started
    lines = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    last = lines[-1] if lines else f"exit {proc.returncode}"
    if labs:
        return ("stubs-fail" if proc.returncode != 0 else "STUBS-PASS"), last, seconds
    return ("ok" if proc.returncode == 0 else "FAIL"), last, seconds


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prefixes", nargs="*")
    p.add_argument("--labs", action="store_true")
    args = p.parse_args(argv)
    found = modules(args.prefixes)
    problems = 0
    for module in found:
        status, last, seconds = run(module, args.labs)
        rel = module.relative_to(ROOT)
        print(f"{status:<11}{str(rel):<42}{seconds:>6.0f}s  {last}", flush=True)
        problems += status in ("FAIL", "STUBS-PASS")
    print(f"\n{len(found)} module(s), {problems} problem(s)" + (" [labs mode: a suite that passes with the stubs selected is the problem]" if args.labs else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
