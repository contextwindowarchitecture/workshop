"""Read a committed Domain 2 run of the viability benchmark from its files: the arms, side by side, with no model.

    uv run domain2_read.py                 # the latest run under the benchmark sibling's domain2/results/d2
    uv run domain2_read.py --run <run-id>

S2 is the suite that sends every arm's payload to one model and grades the answers with no judge. This reads what it
wrote (suites/S2/summary.json): for each arm, how often the model answered right (aptitude), the 95% interval from a
bootstrap over conversations, and how often the fact the probe needed was in the payload at all, which is what
separates a payload failure from a model failure. Needs the `cwa-extended/benchmark` sibling (CWA_SIBLINGS_ROOT).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from siblings import require  # noqa: E402

ORDER = ["control-full", "control-concat", "concat", "truncate", "truncate-pinned", "window", "summary", "cwa-history", "cwa-state-x", "cwa-state", "cwa-memory", "cwa-pipeline"]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run")
    args = p.parse_args(argv)
    results = require("benchmark") / "domain2" / "results" / "d2"
    if not (results / "index.json").exists():
        print(f"no Domain 2 run under {results}: the benchmark commits its model cache, not its results.\n"
              "Replay one at the benchmark root (uv run cwabench --domain 2 run), or read the published table in its docs/domain2.md.")
        return 1
    index = json.loads((results / "index.json").read_text(encoding="utf-8"))
    run_id = args.run or index["latest"]
    run = results / run_id
    top = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    s2 = json.loads((run / "suites" / "S2" / "summary.json").read_text(encoding="utf-8"))
    config = (run / "config.toml").read_text(encoding="utf-8") if (run / "config.toml").exists() else ""
    size = next((line.split("=")[1].split("#")[0].strip().strip('"') for line in config.splitlines() if line.strip().startswith("size")), "?")
    command = json.loads((run / "manifest.json").read_text(encoding="utf-8")).get("command", []) if (run / "manifest.json").exists() else []
    if "--size" in command[:-1]:
        size = command[command.index("--size") + 1]  # the command line overrides config.toml's default
    model = s2.get("model", {})
    print(f"run {run_id}: {top['status']}; size {size}; model {model.get('model')} in {model.get('mode')} mode, {model.get('cache_hits', 0)} cache hits of {model.get('calls', 0)} calls")
    print("S2 scripted conversations, every arm on the same probes. Aptitude is the share of probes answered right.\n")
    rows = {row["arm"]: row for row in s2["by_arm"]}
    tiers = sorted({row.get("tier") for row in s2["by_arm"] if row.get("tier")}, key=str)
    print(f"{'arm':<18}{'tier':<10}{'n':>6}{'aptitude':>10}{'95% interval':>18}{'fact in payload':>17}{'stale':>7}")
    seen = set()
    for arm in ORDER + sorted(set(rows) - set(ORDER)):
        for row in s2["by_arm"]:
            if row["arm"] != arm or (arm, row.get("tier")) in seen:
                continue
            seen.add((arm, row.get("tier")))
            given = row["given"]["present"]
            present = given["n"] / row["n"] if row["n"] else 0
            iv = row.get("interval") or {}
            print(f"{arm:<18}{str(row.get('tier') or ''):<10}{row['n']:>6}{row['aptitude']:>10.3f}{'[' + format(iv.get('low', 0), '.3f') + ', ' + format(iv.get('high', 0), '.3f') + ']':>18}{present:>16.0%}{row['verdicts'].get('stale', 0):>7}")
    if len(tiers) > 1:
        print(f"\ntiers are token budgets or control groups: {', '.join(map(str, tiers))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
