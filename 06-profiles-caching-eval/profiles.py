"""Lab A: the candidate profiles side by side, and the same request rendered under two of them.

    uv run profiles.py list                              # the three placements, slot by slot
    uv run profiles.py diff policy-first cache-first     # placement diff, then the same request under both
    uv run profiles.py render cache-first --turn 3       # one rendered payload, block by block

A profile places slots in order with a wrapper each; the assembler renders in that order. Nothing else changes between
two profiles here: same items, same policy, same budget, same clock. What differs is where the model finds things,
and which bytes a second call repeats (R-19, R-20).
"""

from __future__ import annotations

import argparse
import json
import sys

from app import context
from evaluate import blocks_of, conversations


def placement(profile: dict) -> list[str]:
    return [f"{p['slot']} ({p['wrap']})" for p in profile["placement"]]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["list", "diff", "render"])
    p.add_argument("profiles", nargs="*")
    p.add_argument("--conversation", default="export-then-roles")
    p.add_argument("--turn", type=int, default=2)
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    args = p.parse_args(argv)
    table = context.profiles(args.impl)
    if args.command == "list":
        for pid, profile in table.items():
            print(f"{pid} v{profile['version']}  [{profile['evaluation']['status']}]")
            for n, line in enumerate(placement(profile), start=1):
                print(f"   {n}. {line}")
        return 0
    request = context.turns_of(conversations()[args.conversation])[args.turn - 1]
    if args.command == "render":
        result = context.assemble(context.snapshot(request, table[args.profiles[0]]))
        for block in blocks_of(result.payload):
            print(f"--- {block['id']}\n{block['text']}")
        return 0
    a, b = (table[x] for x in args.profiles[:2])
    print(f"{'#':<3}{a['id']:<44}{b['id']}")
    for n, (x, y) in enumerate(zip(placement(a), placement(b)), start=1):
        print(f"{n:<3}{x:<44}{y}{'' if x == y else '   <- differs'}")
    ra, rb = (context.assemble(context.snapshot(request, pr)) for pr in (a, b))
    print(f"\nsame request, turn {args.turn} of {args.conversation}:")
    for pr, r in ((a, ra), (b, rb)):
        ids = [blk["id"] for blk in blocks_of(r.payload)]
        print(f"  {pr['id']}: {r.trace['result']['input_tokens']} tokens, sha256 {r.trace['result']['hash'][:12]}, blocks {ids}")
    same = sum(1 for x, y in zip(ra.trace["included"], rb.trace["included"]) if x == y)
    print(f"  included lists identical: {ra.trace['included'] == rb.trace['included']}; same item set: {sorted(i['item_id'] for i in ra.trace['included']) == sorted(i['item_id'] for i in rb.trace['included'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
