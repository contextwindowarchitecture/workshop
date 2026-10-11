"""Run the tools, adapt their output, freeze, assemble, read the trace.

    uv run run.py --user u_ada "How do I export the whole workspace, including attachments?"
    uv run run.py --impl labs --user u_ada "..."                     # your adapters
    uv run run.py --user u_ada --calls account,status,status "..."   # script MCP calls; a repeated call is superseded
    uv run run.py --user u_ben --calls members "..."                 # a Member asks for a tool the policy grants to Owners and Admins
    uv run run.py --user u_ada --fault silent-sql "..."              # the memory adapter drops rows in its WHERE clause
    uv run run.py --user u_ada --fault specs-as-items "..."          # the MCP adapter emits tool specs itself
    uv run run.py --user u_ada --defaults --payload "..."

The call names: account = get_account for the signed-in workspace; members = list_members; status = get_service_status
for the workspace's region. The application assigns each call's observed_at from its own clock.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cwa import Snapshot, SnapshotError, assemble

import capability_policy
import common
import fixed
import impl
from common import Request
from tools import llama_retriever, mcp_client, memory_db

ASKED_AT = "2026-10-01T10:00:00Z"
USERS = {"u_ada": ("w_kitewood", "Owner", "EU"), "u_ben": ("w_kitewood", "Member", "EU"), "u_cho": ("w_larkspur", "Admin", "US")}
CALLS = {"account": lambda t, r: ("get_account", {"workspace": t}), "members": lambda t, r: ("list_members", {"workspace": t}),
         "status": lambda t, r: ("get_service_status", {"region": r})}


def request(user: str, question: str) -> Request:
    tenant, role, _ = USERS[user]
    return Request(tenant=tenant, user=user, role=role, session="s_w9a", asked_at=ASKED_AT, question=question)


def scripted_calls(user: str, names: list[str]) -> list[mcp_client.Call]:
    tenant, _, region = USERS[user]
    calls = []
    for n, name in enumerate(names, start=1):
        tool, arguments = CALLS[name](tenant, region)
        calls.append(mcp_client.Call(tool, arguments, f"2026-10-01T10:00:{n:02d}Z"))
    return calls


def build(req: Request, calls: list[mcp_client.Call], which: str | None = None, faults: tuple[str, ...] = ()) -> dict[str, Any]:
    """Run every tool, adapt, freeze: the application's job between the request and the assembler."""
    retriever, memory, mcp = (impl.module(m, which) for m in ("retriever_adapter", "memory_adapter", "mcp_adapter"))
    settings = common.policy("assembly.json")
    hits = llama_retriever.retrieve(req.question, settings["retrieval"]["top_k"])
    info, specs, results = mcp_client.session(calls)
    proposed = mcp.proposals(specs)
    capabilities, grant = capability_policy.offer(proposed, req.role, req.asked_at)
    batches = [
        fixed.app_policy(),
        capabilities,
        retriever.adapt(hits, req),
        memory.adapt(memory_db.connect(), req, silent="silent-sql" in faults),
        mcp.observations(info, results, req, specs_as_items=specs if "specs-as-items" in faults else None),
        fixed.chat_session(req),
    ]
    return common.snapshot(req, batches, grant)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question")
    p.add_argument("--user", choices=sorted(USERS), default="u_ada")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    p.add_argument("--calls", default="account,status", help="comma-separated call names, in order (default: account,status)")
    p.add_argument("--fault", action="append", default=[], choices=["silent-sql", "specs-as-items"])
    p.add_argument("--defaults", action="store_true")
    p.add_argument("--payload", action="store_true")
    p.add_argument("--out", help="write the frozen snapshot here")
    args = p.parse_args(argv)
    req = request(args.user, args.question)
    try:
        document = build(req, scripted_calls(args.user, [c for c in args.calls.split(",") if c]), args.impl, tuple(args.fault))
    except NotImplementedError as todo:
        print(f"an adapter is not written yet: {todo}\n  (run with --impl solution to see the finished adapters)")
        return 2
    if args.out:
        Path(args.out).write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        result = assemble(Snapshot.from_json(document))
    except SnapshotError as error:
        print("REJECTED: the snapshot is invalid; no payload, no trace")
        for problem in error.problems:
            print(f"  {problem}")
        return 2
    print(f"impl={impl.name(args.impl)}  user={args.user} ({req.role})  calls={args.calls}  faults={','.join(args.fault) or '-'}\n")
    common.report(document, result, defaults=args.defaults)
    if args.payload and result.payload:
        payload = json.loads(result.payload)
        for entry in payload.get("system", []):
            print("\n-- system --\n" + entry["text"])
        for tool in payload.get("tools", []):
            print("\n-- tool --\n" + json.dumps(tool, ensure_ascii=False))
        for message in payload.get("messages", []):
            print(f"\n-- {message['role']} --\n{message['content']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
