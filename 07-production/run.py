"""The production wrapper around the agent: store every run, emit spans, map refusals to outcomes, and in deployment
mode take the route policy and profile only from the registry.

    uv run run.py --script evals/cases/scripts.json#status-resolved --user u_ada "Is there an incident in our region?"
    uv run run.py --live --user u_ada "Is there an incident in our region?"
    uv run run.py --deployment --live --user u_ada "..."       # refused until the profile is evaluated and locked
    CWA_W7_TRACE_CONSOLE=1 uv run run.py --script ... "..."     # print the spans
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from cwa.registry import Registry, RegistryError

import agent
import impl
import models
import outcomes
import store
import telemetry
from request import Request

HERE = Path(__file__).resolve().parent


def pinned(model_name: str) -> dict[str, Any]:
    """What a deployment may use: the route policy and profile through the registry lock, an evaluated profile only,
    and only the model it was evaluated for (R-19, R-20)."""
    lock_path = HERE / "policy" / "registry.lock.json"
    if not lock_path.exists():
        raise RegistryError(["no policy/registry.lock.json: nothing has been promoted (evals.py promote)"])
    profile = json.loads((HERE / "policy" / "profile.json").read_text(encoding="utf-8"))
    policy = json.loads((HERE / "policy" / "route-policy.json").read_text(encoding="utf-8"))
    registry = Registry.from_json(json.loads(lock_path.read_text(encoding="utf-8")), [profile], [policy])
    chosen = registry.profile(profile["id"], profile["version"], deployment=True)
    if chosen["model_family"] != model_name:
        raise RegistryError([f"profile {chosen['id']} v{chosen['version']} was evaluated for {chosen['model_family']}, not {model_name}"])
    return {"profile": chosen, "route_policy": registry.route_policy(policy["route"], policy["version"])}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("question")
    p.add_argument("--user", default="u_ada")
    p.add_argument("--script", help="scripts file, optionally #case-id for a file of many scripts")
    p.add_argument("--live", action="store_true")
    p.add_argument("--fault", action="append", default=[], choices=["injected-response", "error"])
    p.add_argument("--deployment", action="store_true")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    args = p.parse_args(argv)
    if args.live:
        if not models.configured():
            print("--live needs OPENAI_BASE_URL", file=sys.stderr)
            return 2
        model: Any = models.LiveModel(agent.settings()["reserved_output"])
    elif args.script:
        path, _, case = args.script.partition("#")
        scripts = json.loads(Path(path).read_text(encoding="utf-8"))
        model = models.ScriptedModel({"name": f"scripted:{case or 'script'}", **(scripts[case] if case else scripts)})
    else:
        p.error("--script FILE[#case] or --live")
    if args.deployment:
        try:
            agent.PINNED = pinned(getattr(model, "name", "scripted"))
        except RegistryError as error:
            print("deployment refused:\n  " + "\n  ".join(error.problems))
            return 1
    request = Request(user=args.user, session=f"s_{uuid.uuid4().hex[:8]}", asked_at="2026-10-01T10:00:00Z", question=args.question)
    record = asyncio.run(agent.run(request, model, faults=tuple(args.fault)))
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    store.save(store.connect(), run_id, record, deployment=args.deployment)
    spans = telemetry.emit(run_id, record, args.impl)
    last = record["inferences"][-1]["trace"]
    if last["refused"]["bool"]:
        o = outcomes.outcome(last["refused"]["reason"], (last.get("recovery") or {}).get("action"))
        print(f"\nrefused {last['refused']['reason']}: outcome {o.action}\n  user sees: {o.user_message}\n  operator: {o.operator_note}")
    print(f"\nstored as {run_id} ({len(record['inferences'])} inference(s)); {spans} span(s) emitted")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
