"""What drafts the reply: a scripted drafter for recorded, replayable runs, or a live OpenAI-compatible model.

Both take the assembled payload and return the model's text, which the route's contract says must be JSON. The scripted
drafter returns the draft its script holds for the case, so every committed run is model-free; the live drafter hands
the payload over unchanged (§1). The routes render cwa-message-blocks/v1, so a user message is a list of blocks, one
per item, which the live drafter joins with nothing between them.
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


def text_of(content: Any) -> str:
    return content if isinstance(content, str) else "".join(block["text"] for block in content)


class LiveDrafter:
    def __init__(self, reserved_output: int) -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ.get("OPENAI_API_KEY", "none"))
        self.name = os.environ.get("CWA_WORKSHOP_MODEL", "local-model")
        self.reserved_output = reserved_output

    def draft_for(self, payload: bytes) -> str:
        rendered = json.loads(payload)
        messages = [{"role": "system", "content": e["text"]} for e in rendered.get("system", [])]
        messages += [{"role": m["role"], "content": text_of(m["content"])} for m in rendered["messages"]]
        request: dict[str, Any] = {"model": self.name, "messages": messages, "max_tokens": self.reserved_output}
        if rendered.get("tools"):
            request["tools"] = [{"type": "function", "function": t} for t in rendered["tools"]]
        if os.environ.get("CWA_WORKSHOP_REASONING_EFFORT"):
            request["reasoning_effort"] = os.environ["CWA_WORKSHOP_REASONING_EFFORT"]
        return self.client.chat.completions.create(**request).choices[0].message.content or ""


def configured() -> bool:
    return bool(os.environ.get("OPENAI_BASE_URL"))
