#!/usr/bin/env python3
"""Every repository check in one run, in the order a facilitator or CI runs them.

    python3 shared/tools/check_all.py            # everything: contract, lint, links, glossary, site links, scenarios, tests (both modes), invariants
    python3 shared/tools/check_all.py --quick    # the fast ones only: contract, lint, links, glossary, site links, scenarios

Each step is one of the scripts beside this one, run as a subprocess with its own output shown, and the summary at the
end says which passed. The glossary and site-link checks need the website sibling and the invariants need
11-benchmarking's environment; they report "skip" when their prerequisite is missing rather than failing the run. Standard library only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "shared" / "tools"
sys.path.insert(0, str(ROOT / "shared"))
from siblings import sibling  # noqa: E402


def step(name: str, command: list[str], cwd: Path = ROOT) -> tuple[str, float]:
    print(f"\n=== {name}: {' '.join(command)}", flush=True)
    started = time.monotonic()
    code = subprocess.run(command, cwd=cwd).returncode
    return ("ok" if code == 0 else "FAIL"), time.monotonic() - started


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quick", action="store_true")
    args = p.parse_args(argv)
    py = sys.executable
    results: list[tuple[str, str, float]] = []
    results.append(("siblings present", *step("siblings present", [py, str(ROOT / "shared" / "siblings.py")])))
    results.append(("contract matches its lock", *step("contract matches its lock", [py, str(TOOLS / "vendor_contract.py"), "--verify"])))
    results.append(("no participant code assembles", *step("no participant code assembles", [py, str(TOOLS / "lint_no_assemble.py")])))
    results.append(("relative links resolve", *step("relative links resolve", [py, str(TOOLS / "check_links.py")])))
    if sibling("website").is_dir():
        results.append(("glossary current", *step("glossary current", [py, str(TOOLS / "glossary.py"), "--check"])))
        results.append(("site links resolve", *step("site links resolve", [py, str(TOOLS / "check_site_links.py")])))
    else:
        results.append(("glossary current", "skip (website sibling not checked out)", 0.0))
        results.append(("site links resolve", "skip (website sibling not checked out)", 0.0))
    results.append(("committed scenarios current", *step("committed scenarios current", [py, str(TOOLS / "check_scenarios.py")])))
    if not args.quick:
        results.append(("every suite passes (solution)", *step("every suite passes (solution)", [py, str(TOOLS / "run_tests.py")])))
        results.append(("every suite fails with the stubs", *step("every suite fails with the stubs", [py, str(TOOLS / "run_tests.py"), "--labs"])))
        bench = ROOT / "11-benchmarking"
        results.append(("invariants over every snapshot", *step("invariants over every snapshot", ["uv", "run", "--quiet", "invariants.py"], cwd=bench)))
    print("\n" + "=" * 72)
    for name, status, seconds in results:
        print(f"{status:<42}{name:<40}{seconds:>6.0f}s" if len(status) > 6 else f"{status:<8}{name:<40}{seconds:>6.0f}s")
    failed = [n for n, s, _ in results if s == "FAIL"]
    print(f"\n{len(results)} step(s), {len(failed)} failed" + (": " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
