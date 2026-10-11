"""Read a committed examples-bench run from its files, with no model: invariants first, then the construct measures.

    uv run bench_read.py                      # the newest run under the examples sibling's bench/results
    uv run bench_read.py --run <run-id>       # a particular run
    uv run bench_read.py --measure grounding  # one measure by model, with the range across repeats

The bench's own grade.py rebuilds the checks from the record; this reads what it wrote (summary.json) and lays it out
the way the viewer does, so the numbers can be read without serving the viewer. Needs the `examples` sibling
(CWA_SIBLINGS_ROOT); nothing is sent anywhere.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from siblings import require  # noqa: E402

MEASURES = ("invariant", "answer", "grounding", "conflict", "excluded", "untrusted", "actions", "refusal", "claims", "evals")


def runs(results: Path) -> list[Path]:
    return sorted(p for p in results.iterdir() if p.is_dir() and (p / "summary.json").exists())


def load(run: Path) -> dict:
    return json.loads((run / "summary.json").read_text(encoding="utf-8"))


def by_model(summary: dict) -> dict[str, dict[str, list[int]]]:
    """model -> measure -> [passed, total], summed over every job."""
    out: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for job in summary["jobs"]:
        for measure, (passed, total) in job.get("measures", {}).items():
            out[job["model"]][measure][0] += passed
            out[job["model"]][measure][1] += total
    return out


def repeats(summary: dict, measure: str) -> dict[str, list[float]]:
    """model -> pass rate of the measure per repeat, so a range can be read beside the average."""
    per: dict[str, dict[int, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for job in summary["jobs"]:
        if measure in job.get("measures", {}):
            p, t = job["measures"][measure]
            per[job["model"]][job["repeat"]][0] += p
            per[job["model"]][job["repeat"]][1] += t
    return {m: [p / t for p, t in sorted(v.values()) if t] for m, v in per.items()}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run")
    p.add_argument("--measure")
    args = p.parse_args(argv)
    results = require("examples") / "bench" / "results"
    available = runs(results)
    if not available:
        print(f"no graded runs under {results}")
        return 1
    run = results / args.run if args.run else available[-1]
    summary = load(run)
    print(f"run {summary['run']}: {len(summary['models'])} models, {len(summary['jobs'])} jobs, spent ${summary['spent']:.2f} of ${summary['max_cost_usd']:.2f}")
    print(f"assembler {summary['assembler'][0]['tag']} ({summary['assembler'][0]['commit'][:7]}) for every example\n")
    table = by_model(summary)
    inv_failed = sum(t - p for m in table.values() for p, t in [m["invariant"]])
    print(f"invariants: {sum(m['invariant'][0] for m in table.values())} of {sum(m['invariant'][1] for m in table.values())} passed"
          + ("" if inv_failed == 0 else f"  ({inv_failed} FAILED: a bug in an example or the assembler, not a finding about a model)") + "\n")
    if args.measure:
        print(f"{args.measure} by model: average, then the lowest and highest repeat")
        for model, rates in sorted(repeats(summary, args.measure).items()):
            if rates:
                print(f"  {model:<42}{sum(rates) / len(rates):>7.3f}   [{min(rates):.3f}, {max(rates):.3f}] over {len(rates)} repeats")
        return 0
    measures = [m for m in MEASURES if any(m in row for row in table.values())]
    print(f"{'model':<42}" + "".join(f"{m:>11}" for m in measures))
    for model, row in sorted(table.items()):
        print(f"{model:<42}" + "".join(f"{row[m][0]}/{row[m][1]:<4}".rjust(11) if m in row else " " * 11 for m in measures))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
