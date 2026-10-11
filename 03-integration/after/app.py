"""Your copy of the application. It starts identical to before/app.py. MIGRATION.md says what to change, step by step,
and `CWA_W3_IMPL=after uv run pytest` tells you how far you have got.

    uv run python -m after.app --user u_ada "How do I export the whole workspace, including attachments?"
    uv run python -m after.app --conversation scenarios/02-ben-plan-conflict/conversation.json

By the end, build_request() freezes a snapshot and assembles it, provider_request() turns the payload into the chat
request with no text of its own, and answer() runs the guards on the reply.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import provider
from request import Request, accounts, corpus, memories

INSTRUCTIONS = Path(__file__).resolve().parent / "policy" / "instructions.md"
TOP_K = 5
MAX_HISTORY_MESSAGES = 6
MAX_OUTPUT_TOKENS = 1024


def build_request(request: Request) -> dict[str, Any]:
    """Everything, pasted into one system string and a message list."""
    _, instructions = corpus.front_matter(INSTRUCTIONS.read_text(encoding="utf-8"))
    db = accounts()
    workspace, member = db["workspaces"][request.tenant], db["users"][request.user]
    account = (f"The user is {member['name']}, a workspace {member['role']}"
               f"{' and a billing admin' if member['billing_admin'] else ''}. Workspace {workspace['name']} is on the "
               f"{workspace['plan']} plan, billed {workspace['billing']}, {workspace['seats']} seats, region {workspace['region']}.")
    remembered = "\n".join(f"- {m['text']}" for m in memories() if m["user"] == request.user) or "- nothing yet"
    hits = corpus.bm25(request.question)[:TOP_K]
    articles = "\n\n".join(f"[{chunk.id}] {chunk.text}" for chunk, _ in hits)
    system = (f"{instructions}\n\nAccount:\n{account}\n\nThings I remember about this user:\n{remembered}"
              f"\n\nHelp-center articles:\n\n{articles}")
    messages = [{"role": "system", "content": system}]
    messages += [{"role": t.role, "content": t.text} for t in request.turns[-MAX_HISTORY_MESSAGES:]]
    messages.append({"role": "user", "content": request.question})
    return {"model": provider.model(), "messages": messages, "max_tokens": MAX_OUTPUT_TOKENS}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question", nargs="?")
    p.add_argument("--user", default="u_ada")
    p.add_argument("--conversation", help="a conversation file; overrides --user and the question")
    args = p.parse_args(argv)
    if args.conversation:
        request = Request.load(args.conversation)
    elif args.question:
        request = Request(user=args.user, session="s_before", asked_at="2026-10-01T10:00:00Z", question=args.question)
    else:
        p.error("a question or --conversation")
    reply = provider.send(build_request(request))
    if reply is not None:
        print("\n" + reply)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
