"""The orchestrator: select the route, assemble (escalating when the small tier refuses for protected content), draft,
parse the route's contract, screen, and write the outcome. Given; it calls the modules your team writes.

    uv run app.py --conversation evals/cases/01-holdings-question/conversation.json --draft evals/cases/01-holdings-question/draft.json
    uv run app.py --impl skeleton --conversation ... --draft ...
    uv run app.py --live --conversation ...

The orchestrator never assembles and never edits a payload. It freezes a snapshot per attempt, hands the payload to the
drafter unchanged, treats the draft as untrusted text until it has been parsed and screened, queues actions for the
client's confirmation only after the screens pass, and writes the outcome itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, TextIO

import common
import impl
import models
from common import Request

CONTRACTS = {"portfolio": {"answer", "figures", "citations", "actions"}, "triage": {"summary", "urgency", "team", "citations", "actions"}}
OUTCOMES = {"answered", "case_opened", "needs_advisor"}
FALLBACK = "The assistant could not complete this request safely. Your advisor has been asked to pick it up and will contact you."
RISK = re.compile(r"Risk screen for this session: (\w+)\.")


def report(document: dict[str, Any], trace: dict[str, Any], out: TextIO) -> None:
    route, tier = document["route_policy"]["route"], "small" if document["budget"]["input"] < 5000 else "large"
    if trace["refused"]["bool"]:
        rec = (trace.get("recovery") or {}).get("action")
        print(f"[{route}/{tier}] refused {trace['refused']['reason']}" + (f", recovery {rec}" if rec else ""), file=out)
        return
    gone = [(r["item_id"], r["reason"]) for r in trace["excluded"]]
    conf = [(c["group_id"], c["decided_by"], c.get("winner")) for c in trace["conflicts"]]
    print(f"[{route}/{tier}] {trace['result']['input_tokens']} tokens of {trace['budget']['input']}; {len(trace['included'])} included"
          + (f"; excluded {gone}" if gone else "") + (f"; conflicts {conf}" if conf else ""), file=out)


def risk_decided(document: dict[str, Any], trace: dict[str, Any]) -> str:
    """The risk level the application wrote into state, read back from the included risk item."""
    items = {i["id"]: i for b in document["batches"] for i in b["items"]}
    for r in trace["included"]:
        if r["item_id"].startswith("risk:") and (m := RISK.search(items[r["item_id"]]["body"])):
            return m.group(1)
    return "low"


def unfenced(draft: str) -> str:
    """A model that wraps its JSON in a Markdown fence still answered in JSON; the fence is not part of the contract."""
    text = draft.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def run(request: Request, drafter: Any, which: str | None = None, out: TextIO = sys.stdout, budget_input: int | None = None) -> dict[str, Any]:
    intent, producers, context, guards = (impl.module(m, which) for m in ("intent", "producers", "context", "guards"))
    table = common.routes()
    classified = intent.classify(request.question)
    route = table["intents"][classified.route]
    record: dict[str, Any] = {"request": {"client": request.client, "account": request.account, "session": request.session, "asked_at": request.asked_at,
                                          "question": request.question, "device": request.device, "faults": sorted(request.faults)},
                              "intent": {"route": classified.route, "matched": classified.matched}, "route": route, "attempts": [], "draft": None,
                              "parsed": None, "guards": [], "reply": None, "actions_queued": [], "outcome": None, "model": getattr(drafter, "name", "?")}
    tier, override = "small", budget_input
    result = None
    while tier:
        document = context.snapshot(request, route, tier, budget_input=override)
        result = context.assemble(document)
        trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
        report(document, trace, out)
        record["attempts"].append({"tier": tier, "snapshot": document, "trace": trace, "payload": result.payload.decode("utf-8") if result.payload else None})
        if not result.refused:
            break
        tier = table["escalate"].get(tier, {}).get(trace["refused"]["reason"])
        override = None
    if result is None or result.payload is None:
        record["reply"], record["outcome"] = FALLBACK, "needs_advisor"
        print(f"no payload: outcome needs_advisor; reply: {FALLBACK}", file=out)
        return record
    draft = drafter.draft_for(result.payload)
    record["draft"] = draft
    try:
        parsed = json.loads(unfenced(draft))
        assert isinstance(parsed, dict) and set(parsed) == CONTRACTS[route]
        assert isinstance(parsed["citations"], list) and isinstance(parsed["actions"], list)
    except (ValueError, AssertionError, TypeError, KeyError):
        record["guards"].append({"name": "output_contract", "ok": False, "reason": "the draft is not the JSON the contract requires"})
        record["reply"], record["outcome"] = FALLBACK, "needs_advisor"
        print("draft violates the output contract: needs_advisor", file=out)
        return record
    record["parsed"] = parsed
    final = record["attempts"][-1]
    sent = {r["item_id"] for r in final["trace"]["included"] if r["slot"] == "evidence.knowledge"}
    granted = {r["item_id"].removeprefix("cap:") for r in final["trace"]["included"] if r["slot"] == "governance.capabilities"}
    risk = risk_decided(final["snapshot"], final["trace"])
    decisions = guards.check(parsed, request, route, sent, granted, risk)
    record["guards"] = [{"name": d.name, "ok": d.ok, "reason": d.reason} for d in decisions]
    for d in decisions:
        print(f"guard {d.name}: {'ok' if d.ok else 'FAILED'}, {d.reason}", file=out)
    if all(d.ok for d in decisions):
        record["reply"] = parsed["answer"] if route == "portfolio" else f"{parsed['summary']} (urgency {parsed['urgency']}, {parsed['team']} team)"
        record["actions_queued"] = [a["tool"] for a in parsed["actions"]]  # queued for the client's confirmation or the team; never executed here
        record["outcome"] = "answered" if route == "portfolio" else "case_opened"
    else:
        record["reply"], record["outcome"] = FALLBACK, "needs_advisor"
    print(f"reply: {record['reply'][:160]}{'...' if len(record['reply']) > 160 else ''}\nactions queued: {record['actions_queued']}\noutcome: {record['outcome']} (written by the application)", file=out)
    return record


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--conversation", required=True)
    p.add_argument("--draft", help="a scripted draft JSON file; omit with --live")
    p.add_argument("--live", action="store_true")
    p.add_argument("--impl", choices=["skeleton", "solution"], default=None)
    p.add_argument("--budget", type=int, help="override budget.input on the first attempt")
    p.add_argument("--record", metavar="FILE")
    args = p.parse_args(argv)
    request = Request.load(args.conversation)
    if args.live:
        if not models.configured():
            print("--live needs OPENAI_BASE_URL", file=sys.stderr)
            return 2
        drafter: Any = models.LiveDrafter(common.budget("large")["reserved_output"])
    elif args.draft:
        drafter = models.ScriptedDrafter(json.loads(Path(args.draft).read_text(encoding="utf-8")), f"scripted:{Path(args.draft).parent.name}")
    else:
        p.error("--draft FILE or --live")
    try:
        record = run(request, drafter, args.impl, budget_input=args.budget)
    except NotImplementedError as todo:
        print(f"not written yet: {todo}")
        return 2
    if args.record:
        Path(args.record).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
