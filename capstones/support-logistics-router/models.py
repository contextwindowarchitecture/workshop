"""What drafts the reply: a scripted drafter for recorded, replayable runs, or a live OpenAI-compatible model.

Both take the assembled payload and return the model's text, which the output contract says must be JSON with reply,
next_stage and citations. The scripted drafter returns the draft its script holds for the case, so every committed run
is model-free; the live drafter hands the payload over unchanged (§1).
"""

from __future__ import annotations

import json
import os
from typing import Any


class ScriptedDrafter:
    def __init__(self, draft: dict[str, Any], name: str = "scripted") -> None:
        self.draft, self.name = draft, name

    def draft_for(self, payload: bytes) -> str:
        return json.dumps(self.draft, ensure_ascii=False)


class LiveDrafter:
    def __init__(self, reserved_output: int) -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ.get("OPENAI_API_KEY", "none"))
        self.name = os.environ.get("CWA_WORKSHOP_MODEL", "local-model")
        self.reserved_output = reserved_output

    def draft_for(self, payload: bytes) -> str:
        rendered = json.loads(payload)
        messages = [{"role": "system", "content": e["text"]} for e in rendered.get("system", [])]
        messages += [{"role": m["role"], "content": m["content"]} for m in rendered["messages"]]
        request: dict[str, Any] = {"model": self.name, "messages": messages, "max_tokens": self.reserved_output}
        if rendered.get("tools"):
            # the offered tools are shown to the model as the API's tool definitions, but a call is a JSON action the
            # contract names and the guards read, never a native tool call: tool_choice none keeps it that way
            request["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""), "parameters": t["input_schema"]}} for t in (json.loads(e["text"]) for e in rendered["tools"])]
            request["tool_choice"] = "none"
        if os.environ.get("CWA_WORKSHOP_REASONING_EFFORT"):
            request["reasoning_effort"] = os.environ["CWA_WORKSHOP_REASONING_EFFORT"]
        return self.client.chat.completions.create(**request).choices[0].message.content or ""


def configured() -> bool:
    return bool(os.environ.get("OPENAI_BASE_URL"))
