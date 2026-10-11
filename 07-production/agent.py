"""W5's bounded agent loop, unchanged in substance: one snapshot per inference, a guard on every call, a denial returned as
state, and a record of everything. run.py wraps it with the store, telemetry and the deployment gate.

    uv run agent.py --script scripts/01-status-check.json --user u_ada "Is there an incident in our region?"
    uv run agent.py --script scripts/03-injected-instruction.json --fault injected-response --user u_ada "..."
    uv run agent.py --live --user u_ada "Is there an incident in our region?"        # needs OPENAI_BASE_URL
    uv run agent.py --replay scenarios/03-injected-instruction/run.json              # re-assemble every inference

Per inference: run every producer, offer tools through the capability policy, freeze, assemble, hand the payload to the
model. Tool calls go through the guard; approved ones go to the MCP server and come back as observations on the next
inference, denied ones come back as task state saying why. At most max_turns inferences; on the last, no tools.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, TextIO

from cwa import Snapshot, assemble

import capability_policy
import guard
import models
import producers
from producers import Step
from request import Request
from tools.mcp_client import Session

POLICY = Path(__file__).resolve().parent / "policy"


def settings() -> dict[str, Any]:
    return json.loads((POLICY / "assembly.json").read_text(encoding="utf-8"))


def policy(name: str) -> Any:
    return json.loads((POLICY / name).read_text(encoding="utf-8"))


class Clock:
    """The application's clock: read once per inference and once per call, never by a producer."""

    def __init__(self, start: str) -> None:
        self.at = start

    def tick(self, seconds: int = 1) -> str:
        from datetime import datetime, timedelta, timezone
        t = datetime.fromisoformat(self.at.replace("Z", "+00:00")) + timedelta(seconds=seconds)
        self.at = t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self.at


PINNED: dict[str, Any] | None = None  # set by run.py --deployment: the route policy and profile the registry returned


def snapshot(request: Request, task: str, steps: list[Step], turn: int, now: str, capabilities: dict[str, Any],
             grant: dict[str, Any], server: str, version: str) -> dict[str, Any]:
    s = settings()
    pinned = PINNED or {"profile": policy("profile.json"), "route_policy": policy("route-policy.json")}
    return {
        "assembly_time": now,
        "scope": {"tenant": request.tenant, "user": request.user, "session": request.session, "task": task},
        "budget": {"input": s["model_context_limit"] - s["reserved_output"], "reserved_output": s["reserved_output"], "margin_percent": s["margin_percent"]},
        "profile": pinned["profile"],
        "route_policy": pinned["route_policy"],
        "tokenizer": s["tokenizer"],
        "renderer": s["renderer"],
        "batches": [
            producers.app_policy(),
            capabilities,
            producers.accounts_db(request, now),
            producers.agent_controller(request, task, steps, turn, s["max_turns"], now),
            producers.fernway_accounts(request, task, steps, server, version),
            producers.chat_session(request),
        ],
        "conflicts": [],
        "capabilities": grant,
    }


def report(document: dict[str, Any], trace: dict[str, Any], out: TextIO) -> None:
    turn = document["batches"][3]["items"][0]["source_version"]
    if trace["refused"]["bool"]:
        print(f"turn {turn}: refused {trace['refused']['reason']}", file=out)
        return
    tools = [r["item_id"] for r in trace["included"] if r["slot"] == "governance.capabilities"]
    obs = [r["item_id"] for r in trace["included"] if r["slot"] == "evidence.tool_results"]
    gone = [(r["item_id"], r["reason"]) for r in trace["excluded"]]
    print(f"turn {turn}: {trace['result']['input_tokens']} tokens; tools {tools or 'none'}; observations {obs or 'none'}"
          + (f"; excluded {gone}" if gone else ""), file=out)


async def run(request: Request, model: Any, *, task: str = "t_account", faults: tuple[str, ...] = (), which: str | None = None,
              out: TextIO = sys.stdout) -> dict[str, Any]:
    s = settings()
    clock = Clock(request.asked_at)
    role = producers.accounts()["users"][request.user]["role"]
    steps: list[Step] = []
    record: dict[str, Any] = {"request": {"user": request.user, "session": request.session, "asked_at": request.asked_at, "question": request.question, "faults": sorted(faults)},
                              "model": getattr(model, "name", "?"), "inferences": [], "answer": None}
    async with Session(faults) as api:
        proposed = await api.proposed()
        for turn in range(1, s["max_turns"] + 1):
            now = clock.tick()
            capabilities, grant, granted = capability_policy.offer(proposed, role, now, final_turn=turn == s["max_turns"], which=which)
            document = snapshot(request, task, steps, turn, now, capabilities, grant, api.name, api.version)
            result = assemble(Snapshot.from_json(document))
            trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
            report(document, trace, out)
            inference: dict[str, Any] = {"turn": turn, "snapshot": document, "trace": trace,
                                         "payload": result.payload.decode("utf-8") if result.payload else None, "decision": None, "steps": []}
            record["inferences"].append(inference)
            if result.payload is None:
                record["answer"] = None
                break
            decision = model.decide(result.payload, turn)
            inference["decision"] = {"tool_calls": [asdict(c) for c in decision.tool_calls], "answer": decision.answer}
            if decision.answer is not None or not decision.tool_calls:
                record["answer"] = decision.answer
                print(f"answer: {decision.answer}", file=out)
                break
            for call in decision.tool_calls:
                verdict = guard.authorize(call.name, call.arguments, granted, document["scope"])
                step = Step(turn, call.name, call.arguments, verdict.approved, verdict.reason)
                if verdict.approved:
                    try:
                        outcome = await asyncio.wait_for(api.call(call.name, call.arguments), timeout=s["tool_timeout_seconds"])
                        step = Step(turn, call.name, call.arguments, True, verdict.reason, True, outcome.ok, outcome.value, clock.tick())
                    except asyncio.TimeoutError:
                        step = Step(turn, call.name, call.arguments, True, verdict.reason, True, False, f"no answer within {s['tool_timeout_seconds']} s", clock.tick())
                print(f"  {call.name}({json.dumps(call.arguments)}): {'approved' if step.approved else 'DENIED'}, {step.reason}"
                      + (f" -> {'ok' if step.ok else 'error'}" if step.executed else ""), file=out)
                steps.append(step)
                inference["steps"].append(asdict(step))
    return record


def replay(path: Path, out: TextIO = sys.stdout) -> bool:
    """Re-assemble every recorded inference and compare bytes: the model is not needed (R-23)."""
    record = json.loads(path.read_text(encoding="utf-8"))
    same = True
    for inference in record["inferences"]:
        result = assemble(Snapshot.from_json(inference["snapshot"]))
        payload = result.payload.decode("utf-8") if result.payload else None
        trace = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
        ok = payload == inference["payload"] and trace == inference["trace"]
        same &= ok
        print(f"turn {inference['turn']}: {'same bytes, same trace' if ok else 'DIFFERS'}  digest {trace['context']['snapshot_digest'][:16]}", file=out)
    return same


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question", nargs="?")
    p.add_argument("--user", default="u_ada")
    p.add_argument("--script", help="a scripted model: scripts/<name>.json")
    p.add_argument("--live", action="store_true", help="an OpenAI-compatible model from OPENAI_BASE_URL")
    p.add_argument("--fault", action="append", default=[], choices=["injected-response", "error"])
    p.add_argument("--record", metavar="FILE", help="write the run record here")
    p.add_argument("--replay", metavar="RUN", help="re-assemble a recorded run and compare")
    args = p.parse_args(argv)
    if args.replay:
        return 0 if replay(Path(args.replay)) else 1
    if not args.question:
        p.error("a question")
    request = Request(user=args.user, session="s_w5", asked_at="2026-10-01T10:00:00Z", question=args.question)
    if args.live:
        if not models.configured():
            print("--live needs OPENAI_BASE_URL; see docs/providers/openai-compatible.md", file=sys.stderr)
            return 2
        model: Any = models.LiveModel(settings()["reserved_output"])
    elif args.script:
        model = models.ScriptedModel(json.loads(Path(args.script).read_text(encoding="utf-8")))
    else:
        p.error("--script FILE or --live")
    try:
        record = asyncio.run(run(request, model, faults=tuple(args.fault)))
    except NotImplementedError as todo:
        print(f"the guard is not written yet: {todo}")
        return 2
    if args.record:
        Path(args.record).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"recorded {args.record}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
