"""What decides the next step: a scripted model for recorded, replayable runs, or a live OpenAI-compatible model.

Both take the assembled payload and return a Decision: tool calls to make, or an answer. The scripted model reads a
script of turns, so every committed scenario runs without a model and reaches the same decisions; the live model turns
the payload into a chat request with tools and reads tool_calls back.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Decision:
    tool_calls: tuple[ToolCall, ...] = ()
    answer: str | None = None


class ScriptedModel:
    """turns: [{"tool_calls": [{"name", "arguments"}]} | {"answer": "..."}], consumed one per inference."""

    def __init__(self, script: dict[str, Any]) -> None:
        self.turns = list(script["turns"])
        self.name = script.get("name", "scripted")

    def decide(self, payload: bytes, turn: int) -> Decision:
        if turn - 1 >= len(self.turns):
            return Decision(answer="(the script ended without an answer)")
        step = self.turns[turn - 1]
        if "answer" in step:
            return Decision(answer=step["answer"])
        return Decision(tool_calls=tuple(ToolCall(c["name"], dict(c["arguments"])) for c in step["tool_calls"]))


class LiveModel:
    """An OpenAI-compatible endpoint with tool calling. The payload is handed over unchanged (§1)."""

    def __init__(self, reserved_output: int) -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ.get("OPENAI_API_KEY", "none"))
        self.name = os.environ.get("CWA_WORKSHOP_MODEL", "local-model")
        self.reserved_output = reserved_output

    def decide(self, payload: bytes, turn: int) -> Decision:
        rendered = json.loads(payload)
        messages = [{"role": "system", "content": e["text"]} for e in rendered.get("system", [])]
        messages += [{"role": m["role"], "content": m["content"]} for m in rendered["messages"]]
        request: dict[str, Any] = {"model": self.name, "messages": messages, "max_tokens": self.reserved_output}
        if rendered.get("tools"):
            request["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}} for t in rendered["tools"]]
        if os.environ.get("CWA_WORKSHOP_REASONING_EFFORT"):
            request["reasoning_effort"] = os.environ["CWA_WORKSHOP_REASONING_EFFORT"]
        response = self.client.chat.completions.create(**request)
        message = response.choices[0].message
        if message.tool_calls:
            calls = tuple(ToolCall(c.function.name, json.loads(c.function.arguments or "{}")) for c in message.tool_calls)
            return Decision(tool_calls=calls)
        return Decision(answer=message.content or "")


def configured() -> bool:
    return bool(os.environ.get("OPENAI_BASE_URL"))
