"""Lab D: the specification's budget conformance cases, to predict and run.

    uv run cases.py list                 # every budget-* case with its rules and description; no outcomes
    uv run cases.py run budget-slot-floor   # assemble it with the reference assembler and show the decisions
    uv run cases.py reveal budget-slot-floor   # the expected trace's refusal, exclusions and compressions

The cases are vendored in shared/contract/cwa/conformance/cases/. Each is a snapshot and the trace every conformant
assembler must produce for it. Read the description, predict the outcome, run it, then reveal.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cwa import Snapshot, assemble

CASES = Path(__file__).resolve().parents[1] / "shared" / "contract" / "cwa" / "conformance" / "cases"


def budget_cases() -> list[Path]:
    return sorted(p for p in CASES.iterdir() if p.name.startswith(("budget-", "protected-over", "evidence-")))


def summary(trace: dict) -> str:
    lines = []
    if trace["refused"]["bool"]:
        rec = (trace.get("recovery") or {}).get("action")
        lines.append(f"  REFUSED {trace['refused']['reason']}" + (f"  recovery {rec}" if rec else ""))
    else:
        lines.append(f"  assembled: {trace['result']['input_tokens']} tokens, {len(trace['included'])} included")
    for row in trace["compressed"]:
        lines.append(f"  ~ {row['item_id']}  {row['from']} -> {row['to']}  {row['variant_id']}")
    for row in trace["excluded"]:
        lines.append(f"  - {row['item_id']}  {row['reason']}  [{row['stage']}]")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "list":
        for case in budget_cases():
            meta = json.loads((case / "case.json").read_text(encoding="utf-8"))
            print(f"{case.name}  ({', '.join(meta['rules'])})\n    {meta['description']}\n")
        return 0
    command, name = argv[0], argv[1]
    case = CASES / name
    if command == "run":
        document = json.loads((case / "snapshot.json").read_text(encoding="utf-8"))
        budget = document["budget"]
        print(f"{name}: budget.input {budget['input']}, margin {budget.get('margin_percent', 0)}%, tokenizer {document['tokenizer']}")
        print(summary(assemble(Snapshot.from_json(document)).trace))
        return 0
    if command == "reveal":
        print(f"{name}, expected:")
        print(summary(json.loads((case / "expected.trace.json").read_text(encoding="utf-8"))))
        return 0
    print("usage: cases.py list | run <case> | reveal <case>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
