"""The same assistant after the migration. The producers propose context, the assembler decides what is sent, the
trace records every decision, the payload goes to the provider unchanged, and the guards check the reply.

    uv run python -m solution.app --user u_ada "How do I export the whole workspace, including attachments?"
    uv run python -m solution.app --conversation scenarios/02-ben-plan-conflict/conversation.json
    uv run python -m solution.app --replay scenarios/01-ada-export/snapshot.json

Compare build_request() with the one in before/app.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from cwa import AssemblyResult

import provider
from request import Request
from solution import context, guards


def build_request(request: Request) -> tuple[dict[str, Any], AssemblyResult]:
    document = context.snapshot(request)  # freeze: every producer's proposal, the policy, the clock, the conflicts
    return document, context.assemble(document)  # decide: no I/O, no model call


def provider_request(result: AssemblyResult) -> dict[str, Any] | None:
    """The chat request for an assembled payload, or None on a refusal: nothing is sent (R-17)."""
    if result.payload is None:
        return None
    return provider.request_for(result.payload, provider.model(), context.reserved_output())


def evidence_bodies(document: dict[str, Any], result: AssemblyResult) -> list[str]:
    included = {row["item_id"] for row in result.trace["included"] if row["slot"] == "evidence.knowledge"}
    return [i["body"] for b in document["batches"] for i in b["items"] if i["id"] in included]


def report(document: dict[str, Any], result: AssemblyResult, out: TextIO = sys.stdout) -> None:
    trace = result.trace
    candidates = {i["id"]: i for b in document["batches"] for i in b["items"]}
    if trace["refused"]["bool"]:
        recovery = (trace.get("recovery") or {}).get("action")
        print(f"refused: {trace['refused']['reason']}" + (f", recovery {recovery}" if recovery else "") + ". No request is sent.", file=out)
    else:
        b = trace["budget"]
        print(f"assembled {trace['profile']['id']} v{trace['profile']['version']}: {trace['result']['input_tokens']} input tokens "
              f"of {b['input']} with a {b['margin_percent']}% margin, sha256 {trace['result']['hash'][:12]}", file=out)
    for row in trace["included"]:
        rel = candidates.get(row["item_id"], {}).get("relevance")
        print(f"  + {row['slot']:<22} {row['item_id']:<28} {row['tokens']:>4} tokens" + (f"  relevance {rel:g}" if rel is not None else ""), file=out)
    for row in trace["excluded"]:
        slot = row.get("slot") or candidates.get(row["item_id"], {}).get("slot", "")
        print(f"  - {slot:<22} {row['item_id']:<28} {row['reason']}  [{row['stage']}]", file=out)
    for row in trace["conflicts"]:
        winner = f", winner {row['winner']}" if row.get("winner") else ""
        print(f"  ! {row['kind']:<22} {row['group_id']:<28} {row['resolution']} by {row['decided_by']}{winner}", file=out)
    print(f"  snapshot digest {trace['context']['snapshot_digest'][:16]}", file=out)


def answer(request: Request, out: TextIO = sys.stdout) -> str | None:
    document, result = build_request(request)
    report(document, result, out)
    chat = provider_request(result)
    if chat is None:
        return None
    reply = provider.send(chat)
    if reply is None:
        return None
    for decision in guards.check(reply, request, evidence_bodies(document, result)):
        if not decision.ok:
            print(f"\nguard: {decision.reason}; the reply is withheld", file=out)
            return "I can't confirm that from the articles I have. Please contact support@fernway.example."
    return reply


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question", nargs="?")
    p.add_argument("--user", default="u_ada")
    p.add_argument("--conversation")
    p.add_argument("--replay", metavar="SNAPSHOT", help="re-assemble a stored snapshot and print its decisions")
    args = p.parse_args(argv)
    if args.replay:
        document = json.loads(Path(args.replay).read_text(encoding="utf-8"))
        report(document, context.assemble(document))
        return 0
    if args.conversation:
        request = Request.load(args.conversation)
    elif args.question:
        request = Request(user=args.user, session="s_after", asked_at="2026-10-01T10:00:00Z", question=args.question)
    else:
        p.error("a question, --conversation or --replay")
    reply = answer(request)
    if reply is not None:
        print("\n" + reply)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
