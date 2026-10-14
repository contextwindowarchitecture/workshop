"""Read a Domain 2 run of the viability benchmark from its files: the arms, side by side, with no model.

    uv run domain2_read.py                           # the recorded run of 2026-10-12, vendored under data/domain2/
    uv run domain2_read.py --sibling                 # the latest run under the benchmark sibling's domain2/results/d2
    uv run domain2_read.py --sibling --run <run-id>

S2 is the suite that sends every arm's payload to one model and grades the answers with no judge. This reads what it
wrote (suites/S2/summary.json): for each arm, how often the model answered right (aptitude), the 95% interval from a
bootstrap over conversations, the paired difference from truncate-pinned on the same probes, and how often the fact the
probe needed was in the payload at all, which is what separates a payload failure from a model failure. The benchmark
commits its model cache, not its results, so the recorded run's S2 summary is vendored here; --sibling reads a run you
replayed in the `cwa-extended/benchmark` sibling (CWA_SIBLINGS_ROOT, CWA_SIBLING_BENCHMARK).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from siblings import require  # noqa: E402

VENDORED = HERE / "data" / "domain2" / "20261012T052348Z-4a0ea5d"
ORDER = ["control-full", "control-concat", "concat", "truncate", "truncate-pinned", "window", "summary", "cwa-history", "cwa-state-x", "cwa-state", "cwa-memory", "cwa-pipeline"]


def size_of(manifest: dict[str, Any], config: str = "") -> str:
    """The size the run was started at: the command line's --size, else config.toml's default."""
    command = manifest.get("command", [])
    if "--size" in command[:-1]:
        return command[command.index("--size") + 1]
    return next((line.split("=")[1].split("#")[0].strip().strip('"') for line in config.splitlines() if line.strip().startswith("size")), "?")


def load_vendored(run: Path = VENDORED) -> tuple[str, dict[str, Any], str]:
    s2 = json.loads((run / "S2-summary.json").read_text(encoding="utf-8"))
    return run.name, s2, size_of(json.loads((run / "manifest.json").read_text(encoding="utf-8")))


def load_sibling(run_id: str | None) -> tuple[str, dict[str, Any], str] | None:
    results = require("benchmark") / "domain2" / "results" / "d2"
    if not (results / "index.json").exists():
        print(f"no Domain 2 run under {results}: the benchmark commits its model cache, not its results.\n"
              "Replay one at the benchmark root (uv run cwabench --domain 2 run), or drop --sibling to read the vendored run.")
        return None
    run = results / (run_id or json.loads((results / "index.json").read_text(encoding="utf-8"))["latest"])
    s2 = json.loads((run / "suites" / "S2" / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8")) if (run / "manifest.json").exists() else {}
    config = (run / "config.toml").read_text(encoding="utf-8") if (run / "config.toml").exists() else ""
    return run.name, s2, size_of(manifest, config)


def paired(row: dict[str, Any]) -> str:
    p = row.get("paired")
    if not p:
        return "reference" if row["arm"] == "truncate-pinned" else ""
    iv = p.get("interval") or {}
    return f"{p['difference']:+.3f} [{iv.get('low', 0):+.3f}, {iv.get('high', 0):+.3f}]"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sibling", action="store_true", help="read a run under the benchmark sibling instead of the vendored one")
    p.add_argument("--run", help="with --sibling: a run id (default: the latest)")
    args = p.parse_args(argv)
    loaded = load_sibling(args.run) if args.sibling else load_vendored()
    if loaded is None:
        return 1
    run_id, s2, size = loaded
    model = s2.get("model", {})
    print(f"run {run_id}: {s2['status']}; size {size}; model {model.get('model')} in {model.get('mode')} mode, {model.get('cache_hits', 0)} cache hits of {model.get('calls', 0)} calls")
    print("S2 scripted conversations, every arm on the same probes. Aptitude is the share of probes answered right.\n")
    rows = {row["arm"]: row for row in s2["by_arm"]}
    tiers = sorted({row.get("tier") for row in s2["by_arm"] if row.get("tier")}, key=str)
    print(f"{'arm':<18}{'tier':<10}{'n':>6}{'aptitude':>10}{'95% interval':>18}  {'vs truncate-pinned':<26}{'fact in payload':>15}{'stale':>7}")
    seen = set()
    for arm in ORDER + sorted(set(rows) - set(ORDER)):
        for row in s2["by_arm"]:
            if row["arm"] != arm or (arm, row.get("tier")) in seen:
                continue
            seen.add((arm, row.get("tier")))
            given = row["given"]["present"]
            present = given["n"] / row["n"] if row["n"] else 0
            iv = row.get("interval") or {}
            print(f"{arm:<18}{str(row.get('tier') or ''):<10}{row['n']:>6}{row['aptitude']:>10.3f}"
                  f"{'[' + format(iv.get('low', 0), '.3f') + ', ' + format(iv.get('high', 0), '.3f') + ']':>18}  {paired(row):<26}"
                  f"{present:>15.0%}{row['verdicts'].get('stale', 0):>7}")
    if len(tiers) > 1:
        print(f"\ntiers are token budgets or control groups: {', '.join(map(str, tiers))}; the paired difference is at the same budget")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
