"""Lab A: read each summary against the paragraph it summarises, and approve or reject it.

    uv run review.py                 # every paragraph with its summary and your current decision (labs/reviewed.json)
    uv run review.py --impl solution # the reviewed list, with the four rejections and their reasons
    uv run review.py --only refunds  # one article

A summary that will stand in for a paragraph under budget pressure is evidence the model reads. If it says something
the paragraph does not, the model will say it too, and the trace will show a faithful swap of a variant that was
anything but. Four of the thirty-six are wrong. Find them, move them to "rejected" with a reason, and the producer
stops attaching them (R-18).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import impl
from request import corpus

SUMMARIES = Path(__file__).resolve().parent / "summaries" / "summaries.json"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    p.add_argument("--only", help="an article id, such as refunds")
    args = p.parse_args(argv)
    which = args.impl or os.environ.get("CWA_W4_IMPL") or "labs"  # a reviewer reads their own list unless told otherwise
    table = json.loads(SUMMARIES.read_text(encoding="utf-8"))
    review = json.loads(impl.path("reviewed.json", which).read_text(encoding="utf-8"))
    approved, rejected = set(review["approved"]), review.get("rejected", {})
    for chunk in corpus.chunks():
        if args.only and chunk.article != args.only:
            continue
        entry = table.get(hashlib.sha256(chunk.text.encode("utf-8")).hexdigest())
        if not entry:
            continue
        status = "APPROVED" if chunk.id in approved else f"REJECTED: {rejected.get(chunk.id, '')}" if chunk.id in rejected else "undecided"
        print(f"{chunk.id}  [{status}]\n  paragraph: {chunk.text}\n  summary:   {entry['body']}\n")
    print(f"{len(approved)} approved, {len(rejected)} rejected ({impl.name(which)}/reviewed.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
