"""The briefing: the triage snapshot frozen by the producers, assembled, and handed to the runtime as an agent
definition and a prompt, with what was left out and why.

    uv run after.py                 # the briefing from fixtures/issue-7811.json under fullsend-triage/v1 at 24,000 tokens
    uv run after.py --compare       # and the agreement with what the Go integration committed (expected/go-records.json)
    CWA_W9D_IMPL=labs uv run after.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import briefing
import impl

HERE = Path(__file__).resolve().parent
BUDGET_INPUT = 24_000


def build(which: str | None = None) -> tuple[dict, object]:
    producers = impl.module("producers", which)
    route, profile = briefing.registry("fullsend-triage/v1")
    document = producers.triage(briefing.read("issue-7811"), route, profile, BUDGET_INPUT)
    return document, briefing.assemble(document)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--compare", action="store_true")
    args = p.parse_args(argv)
    try:
        document, result = build()
    except NotImplementedError as todo:
        print(f"not written yet: {todo}")
        return 2
    trace = result.trace
    items = {i["id"]: i for b in document["batches"] for i in b["items"]}
    h = briefing.handoff(document, result)
    if result.payload is None:
        print(f"refused {trace['refused']['reason']}: no sandbox starts; attributes {json.dumps(h['attributes'])}")
    else:
        print(f"briefing: {trace['result']['input_tokens']} tokens of {document['budget']['input']}; {len(trace['included'])} items in, {len(trace['excluded'])} out")
        print("\nagent definition (the system entries, joined):")
        for e in json.loads(result.payload)["system"]:
            print(f"  [{e['id']}] {e['text'][:90]}...")
        print("\nprompt (the one user message), by wrapper:")
        for row in trace["included"]:
            if row["slot"] not in ("governance.instructions", "governance.output_contract", "governance.examples"):
                it = items[row["item_id"]]
                print(f"  {row['slot']:<24} {row['item_id']:<40} {it['authority']:<15} {row['tokens']:>4} tokens")
    print("\nleft out, and why:")
    for row in trace["excluded"]:
        who = "its producer" if row["stage"] == "producer" else "the assembler"
        extra = f", keeps {row['duplicate_of']}" if row.get("duplicate_of") else ""
        print(f"  {row['item_id']:<40} {row.get('slot') or '-':<24} {who:<13} {row['reason']}{extra}")
    print(f"\nspan attributes: {json.dumps({k: v for k, v in h['attributes'].items() if k in ('cwa.snapshot_digest', 'cwa.payload.sha256', 'cwa.input_tokens', 'cwa.included', 'cwa.excluded')})}")
    if args.compare:
        go = json.loads((HERE / "expected" / "go-records.json").read_text(encoding="utf-8"))["scenarios"]["triage-7811"]
        same_digest = trace["context"]["snapshot_digest"] == go["snapshot_digest"]
        same_payload = result.payload is not None and hashlib.sha256(result.payload).hexdigest() == go["payload_sha256"]
        print(f"\nagreement with the Go integration (assembler-go): snapshot digest {'same' if same_digest else 'DIFFERS'}; payload bytes {'same' if same_payload else 'DIFFERS'}")
        return 0 if same_digest and same_payload else 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
