"""The account assistant on two routes. It starts on the small route; when that refuses for a reason the route table
escalates, it rebuilds the request on the large route. Each attempt is its own snapshot (R-12, R-23).

    uv run python -m app.app --conversation scenarios/03-pasted-log/conversation.json
    uv run python -m app.app --impl labs --conversation scenarios/03-pasted-log/conversation.json    # your routes table
    uv run python -m app.app --route account-help --conversation ...                                 # start on the large route
    uv run python -m app.app --budget 700 --conversation scenarios/01-export/conversation.json      # squeeze one attempt
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, TextIO

from cwa import AssemblyResult

import provider
from app import context, routes
from request import Request


def report(document: dict[str, Any], result: AssemblyResult, out: TextIO = sys.stdout) -> None:
    trace = result.trace
    candidates = {i["id"]: i for b in document["batches"] for i in b["items"]}
    route = document["route_policy"]["route"]
    if trace["refused"]["bool"]:
        recovery = (trace.get("recovery") or {}).get("action")
        print(f"[{route}] refused: {trace['refused']['reason']}" + (f", recovery {recovery}" if recovery else "") + ". No request is sent.", file=out)
    else:
        b = trace["budget"]
        print(f"[{route}] assembled {trace['profile']['id']} v{trace['profile']['version']}: {trace['result']['input_tokens']} input tokens "
              f"of {b['input']} with a {b['margin_percent']}% margin, sha256 {trace['result']['hash'][:12]}", file=out)
    for row in trace["included"]:
        rel = candidates.get(row["item_id"], {}).get("relevance")
        print(f"  + {row['slot']:<22} {row['item_id']:<28} {row['tokens']:>4} tokens" + (f"  relevance {rel:g}" if rel is not None else ""), file=out)
    for row in trace["compressed"]:
        print(f"  ~ {row['slot']:<22} {row['item_id']:<28} {row['from']:>4} -> {row['to']} tokens  {row['variant_id']}", file=out)
    for row in trace["excluded"]:
        slot = row.get("slot") or candidates.get(row["item_id"], {}).get("slot", "")
        print(f"  - {slot:<22} {row['item_id']:<28} {row['reason']}  [{row['stage']}]", file=out)
    for row in trace["conflicts"]:
        print(f"  ! {row['kind']:<22} {row['group_id']:<28} {row['resolution']} by {row['decided_by']}", file=out)
    print(f"  snapshot digest {trace['context']['snapshot_digest'][:16]}", file=out)


def attempts(request: Request, route: str | None = None, which: str | None = None, budget_input: int | None = None,
             out: TextIO | None = None) -> list[tuple[str, dict[str, Any], AssemblyResult]]:
    """Assemble on the starting route, then on each route the table escalates to, until one assembles or none is left.
    Every attempt is a new snapshot; nothing from a refused attempt is reused."""
    route = route or routes.default(which)
    made = []
    while route:
        document = context.snapshot(request, route, which, budget_input)
        result = context.assemble(document)
        made.append((route, document, result))
        if out:
            report(document, result, out)
        if not result.refused:
            break
        route = routes.next_route(route, result.trace["refused"]["reason"], which)
        budget_input = None  # an override applies to the first attempt only
    return made


def answer(request: Request, route: str | None = None, which: str | None = None, budget_input: int | None = None,
           out: TextIO = sys.stdout) -> str | None:
    final_route, _, result = attempts(request, route, which, budget_input, out)[-1]
    if result.payload is None:
        return None
    chat = provider.request_for(result.payload, routes.model(final_route, which), routes.budget(final_route, which)["reserved_output"])
    return provider.send(chat)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question", nargs="?")
    p.add_argument("--user", default="u_ada")
    p.add_argument("--conversation")
    p.add_argument("--route", help="start on this route instead of the table's default")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    p.add_argument("--budget", type=int, help="override budget.input on the first attempt")
    args = p.parse_args(argv)
    if args.conversation:
        request = Request.load(args.conversation)
    elif args.question:
        request = Request(user=args.user, session="s_w4", asked_at="2026-10-01T10:00:00Z", question=args.question)
    else:
        p.error("a question or --conversation")
    reply = answer(request, args.route, args.impl, args.budget)
    if reply is not None:
        print("\n" + reply)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
