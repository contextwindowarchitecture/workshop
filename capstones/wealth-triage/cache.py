"""Cache-stable placement, measured: over a frozen conversation, how many leading blocks of turn n reappear unchanged
at the head of turn n+1, under the committed profile and under a history-first alternative.

    uv run cache.py                                  # conversations/four-turns.json under both placements
    uv run cache.py --conversation conversations/four-turns.json

A provider's prompt cache reuses an unchanged prefix at block boundaries. The routes render cwa-message-blocks/v1, one
block per item, so the measure is exact: shared leading blocks over blocks in the earlier turn. Placement is a profile
decision (R-19); this is the evidence a profile is promoted on.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import common
import impl
from common import Request, Turn

HERE = Path(__file__).resolve().parent


def turns_of(conversation: dict[str, Any]) -> list[Request]:
    """One request per user turn: the turns before it as history, it as the question."""
    base = {k: conversation[k] for k in ("client", "session")}
    device = conversation.get("device", "known")
    out, history = [], []
    for t in conversation["turns"]:
        if t["role"] == "user":
            out.append(Request(**base, asked_at=t["at"], question=t["text"], turns=tuple(history), device=device))
        history.append(Turn(**t))
    return out


def blocks_of(payload: bytes) -> list[str]:
    rendered = json.loads(payload)
    system = [e["text"] for e in rendered.get("system", [])]
    content = rendered["messages"][0]["content"]
    user = [b["text"] for b in content] if isinstance(content, list) else [content]
    return system + user


def shared_prefix(a: list[str], b: list[str]) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def history_first(profile: dict[str, Any]) -> dict[str, Any]:
    """The same slots with the conversation first: what a chat template does by default."""
    order = ["governance.instructions", "interaction.history", "interaction.query", "state.user", "state.task", "governance.capabilities",
             "evidence.tool_results", "evidence.knowledge", "governance.output_contract"]
    by_slot = {p["slot"]: p for p in profile["placement"]}
    return {**profile, "id": profile["id"] + "-history-first", "placement": [by_slot[s] for s in order if s in by_slot]}


def measure(requests: list[Request], route: str, which: str | None = None, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    context = impl.module("context", which)
    payloads = []
    for r in requests:
        document = context.snapshot(r, route, "large")
        if profile is not None:
            document["profile"] = profile
        result = context.assemble(document)
        assert result.payload is not None, f"turn refused: {result.trace['refused']}"
        payloads.append(blocks_of(result.payload))
    pairs = [{"shared": shared_prefix(a, b), "of": len(a)} for a, b in zip(payloads, payloads[1:])]
    return {"turns": len(payloads), "pairs": pairs, "reuse": sum(p["shared"] for p in pairs) / max(1, sum(p["of"] for p in pairs))}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--conversation", default=str(HERE / "conversations" / "four-turns.json"))
    args = p.parse_args(argv)
    conversation = json.loads(Path(args.conversation).read_text(encoding="utf-8"))
    requests = turns_of(conversation)
    route = conversation.get("route", "portfolio")
    committed = common.policy(route, "profile.json")
    for label, profile in (("committed (cache-first)", None), ("history-first", history_first(committed))):
        m = measure(requests, route, None, profile)
        print(f"{label:<26} reuse {m['reuse']:.0%}: " + ", ".join(f"turn {i + 1}->{i + 2} {p['shared']}/{p['of']} blocks" for i, p in enumerate(m["pairs"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
