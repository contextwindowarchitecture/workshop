"""The committed scenarios: a scripted model's run through the agent, recorded inference by inference.

Each folder under scenarios/ holds scenario.json (user, question, script, faults) and run.json, the record agent.run()
wrote: every inference's snapshot, trace and payload, the model's decision and each tool call with the guard's verdict.
The MCP server runs for real on every build; the script decides what the model does; the clock is the application's.

    uv run scenarios.py --check
    uv run scenarios.py --write
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import agent
import models
from request import Request

SCENARIOS = Path(__file__).parent / "scenarios"
SCRIPTS = Path(__file__).parent / "scripts"
SPECS: dict[str, dict[str, Any]] = {
    "01-status-check": {"user": "u_ada", "question": "Is there an incident in our region right now?", "script": "01-status-check"},
    "02-member-not-offered": {"user": "u_ben", "question": "Who are the billing admins of our workspace?", "script": "02-member-not-offered"},
    "03-injected-instruction": {"user": "u_ada", "question": "Is there an incident in our region right now?", "script": "03-injected-instruction", "faults": ["injected-response"]},
    "04-status-error": {"user": "u_ada", "question": "Is there an incident in our region right now?", "script": "04-status-error", "faults": ["error"]},
    "05-runs-out-of-turns": {"user": "u_ada", "question": "Keep checking until the incident is over.", "script": "05-runs-out-of-turns"},
    "06-wrong-workspace": {"user": "u_ada", "question": "What plan is Larkspur Design on?", "script": "06-wrong-workspace"},
}


def names() -> list[str]:
    return sorted(SPECS)


def _json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def record(name: str) -> dict[str, Any]:
    spec = SPECS[name]
    request = Request(user=spec["user"], session=f"s_{name}", asked_at="2026-10-01T10:00:00Z", question=spec["question"])
    model = models.ScriptedModel(json.loads((SCRIPTS / f"{spec['script']}.json").read_text(encoding="utf-8")))
    import io
    return asyncio.run(agent.run(request, model, faults=tuple(spec.get("faults", [])), which="solution", out=io.StringIO()))


def build(name: str) -> dict[str, bytes | None]:
    return {"scenario.json": _json(SPECS[name]), "run.json": _json(record(name))}


def stale(name: str) -> list[str]:
    found = []
    for file, content in build(name).items():
        path = SCENARIOS / name / file
        if (path.read_bytes() if path.exists() else None) != content:
            found.append(f"{name}/{file}")
    return found


def write(name: str) -> list[str]:
    written = []
    (SCENARIOS / name).mkdir(parents=True, exist_ok=True)
    for file, content in build(name).items():
        path = SCENARIOS / name / file
        if content is not None and (not path.exists() or path.read_bytes() != content):
            path.write_bytes(content)
            written.append(f"wrote {name}/{file}")
    return written


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = p.parse_args(argv)
    if args.write:
        for name in names():
            for line in write(name):
                print(line)
        return 0
    differing = [f for name in names() for f in stale(name)]
    if differing:
        print("stale (run uv run scenarios.py --write, then review the diff):\n  " + "\n  ".join(differing), file=sys.stderr)
        return 1
    print(f"{len(names())} scenarios are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
