"""What every seam shares: W3a's migrated application (its producers, freeze and assembler call), the texts a payload
carries, and the hash that says whether a framework handed the model exactly those texts.

The seam is the one place in a framework where the model's input is built. CWA owns everything before it: the
assembled payload is the input. The framework owns everything after it: the loop, tools, retries, streaming. The
proof that a seam is right is that what reached the model equals what the trace describes, text for text.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
W3A = HERE.parent
sys.path.append(str(W3A))  # after this directory, so W3a's solution/, impl.py and scenarios.py do not shadow ours
from request import Request  # noqa: E402
from solution import context  # noqa: E402

SCENARIOS = W3A / "scenarios"


def scenario_names() -> list[str]:
    return sorted(p.parent.name for p in SCENARIOS.glob("*/conversation.json"))


def scenario(name: str) -> Request:
    return Request.load(SCENARIOS / name / "conversation.json")


def assemble_context(request: Request) -> tuple[dict[str, Any], Any]:
    """W3a's freeze and assemble, unchanged. Every seam calls this and nothing else to build the model's input."""
    document = context.snapshot(request)
    return document, context.assemble(document)


def reserved_output() -> int:
    return context.reserved_output()


def texts_of(payload: bytes) -> dict[str, Any]:
    """The texts a cwa-messages/v1 payload carries: the system entries in order, and the one user message. This is
    what a seam must hand the model, and what a recording model must have received."""
    rendered = json.loads(payload)
    assert len(rendered["messages"]) == 1 and rendered["messages"][0]["role"] == "user", "cwa-messages/v1 renders one user message"
    content = rendered["messages"][0]["content"]
    if isinstance(content, list):
        content = "".join(block["text"] for block in content)
    return {"system": [e["text"] for e in rendered.get("system", [])], "user": content, "tools": [t["name"] for t in rendered.get("tools", [])]}


def joined(texts: dict[str, Any], separator: str = "\n\n") -> dict[str, Any]:
    """The same texts for a framework that takes one system message: the entries joined with one separator, which
    is the only text such a seam adds."""
    return {**texts, "system": [separator.join(texts["system"])] if texts["system"] else []}


def digest(texts: dict[str, Any]) -> str:
    """One hash over the texts, so two sides can be compared in a table."""
    return hashlib.sha256(json.dumps({"system": texts["system"], "user": texts["user"]}, ensure_ascii=False).encode("utf-8")).hexdigest()
