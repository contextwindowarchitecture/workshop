"""Run the producers for one request, freeze the snapshot, assemble it, and read the trace.

    uv run freeze.py --user u_ada "How do I export the whole workspace, including attachments?"
    uv run freeze.py --impl labs --user u_ada "How do I export the whole workspace, including attachments?"     # your producers
    uv run freeze.py --user u_cho --defaults "Can I get a refund on a monthly plan?"  # also list defaults_filled
    uv run freeze.py --user u_ada --budget 700 "How do I export the whole workspace, including attachments?"    # squeeze: variants get used
    uv run freeze.py --user u_ada --fault memory-store-ignores-user "..."            # inject a producer bug
    uv run freeze.py --user u_ada --read-at 2026-10-01T09:50:00Z "..."              # a stale account read
    uv run freeze.py --user u_ada --out snap.json "..."                              # also write the snapshot

The producers propose; this script only freezes what they proposed with the route's policy and hands it to the
assembler. It writes no payload of its own and changes nothing the assembler returns.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import common
import fixed
import impl
from common import Request, Turn

ASKED_AT = "2026-10-01T10:00:00Z"
TENANT = {"u_ada": "w_kitewood", "u_ben": "w_kitewood", "u_cho": "w_larkspur"}


def request(user: str, question: str, *, read_at: str | None = None, faults: tuple[str, ...] = (), history: bool = False) -> Request:
    turns = (
        Turn("user", "Hi, I have a question about our workspace.", "2026-10-01T09:58:00Z"),
        Turn("assistant", "Of course. What would you like to know?", "2026-10-01T09:58:05Z"),
    ) if history else ()
    return Request(tenant=TENANT[user], user=user, session="s_w2demo", asked_at=ASKED_AT, question=question,
                   turns=turns, account_read_at=read_at, faults=frozenset(faults))


def batches(req: Request, which: str | None = None) -> list[dict]:
    retrieval, memory, state = (impl.module(m, which) for m in ("retrieval", "memory", "state"))
    return [fixed.app_policy(), state.accounts_db(req), memory.memory_store(req),
            retrieval.help_center_search(req), fixed.chat_session(req)]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question")
    p.add_argument("--user", choices=sorted(TENANT), default="u_ada")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    p.add_argument("--budget", type=int, help="override budget.input for this run")
    p.add_argument("--read-at", help="when the account row was read (default: when the question was asked)")
    p.add_argument("--fault", action="append", default=[], help="inject a named producer bug")
    p.add_argument("--history", action="store_true", help="include two prior turns")
    p.add_argument("--defaults", action="store_true", help="list every default the assembler filled, per item")
    p.add_argument("--payload", action="store_true", help="print the rendered payload")
    p.add_argument("--out", help="write the frozen snapshot here")
    args = p.parse_args(argv)

    req = request(args.user, args.question, read_at=args.read_at, faults=tuple(args.fault), history=args.history)
    try:
        document = common.snapshot(req, batches(req, args.impl))
    except NotImplementedError as todo:
        print(f"a lab producer is not written yet: {todo}\n  (run with --impl solution to see the finished producers)")
        return 2
    if args.budget:
        document["budget"]["input"] = args.budget
    if args.out:
        Path(args.out).write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    from cwa import Snapshot, SnapshotError, assemble
    try:
        result = assemble(Snapshot.from_json(document))
    except SnapshotError as error:
        print("REJECTED: the snapshot is invalid; no payload, no trace")
        for problem in error.problems:
            print(f"  {problem}")
        return 2
    print(f"impl={impl.name(args.impl)}  user={args.user}  question={args.question!r}\n")
    common.report(document, result, defaults=args.defaults)
    if args.payload and result.payload:
        payload = json.loads(result.payload)
        for entry in payload.get("system", []):
            print("\n-- system --\n" + entry["text"])
        for message in payload.get("messages", []):
            print(f"\n-- {message['role']} --\n{message['content']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
