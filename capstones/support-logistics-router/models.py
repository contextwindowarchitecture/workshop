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
            # The offered tools go to the API as tool definitions so the model sees their schemas (omlx shows the model
            # nothing when tool_choice is "none", so the choice is left to the model). A native tool call is folded
            # into the contract's actions below: the application screens and queues it; nothing is executed here.
            request["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""), "parameters": t["input_schema"]}} for t in (json.loads(e["text"]) for e in rendered["tools"])]
        if os.environ.get("CWA_WORKSHOP_REASONING_EFFORT"):
            request["reasoning_effort"] = os.environ["CWA_WORKSHOP_REASONING_EFFORT"]
        if os.environ.get("CWA_WORKSHOP_EXTRA_BODY"):  # server-specific members, e.g. {"chat_template_kwargs": {"enable_thinking": false}}
            request["extra_body"] = json.loads(os.environ["CWA_WORKSHOP_EXTRA_BODY"])
        message = self.client.chat.completions.create(**request).choices[0].message
        return fold_tool_calls(message.content or "", [(c.function.name, c.function.arguments) for c in (message.tool_calls or [])])


def fold_tool_calls(content: str, calls: list[tuple[str, str]]) -> str:
    """A native tool call becomes an entry in the contract's actions, so the guards see it whichever way the model
    asked. The content must still be the contract's JSON; a model that only called tools has not drafted anything."""
    if not calls:
        return content
    actions = [{"tool": name, "arguments": (json.loads(arguments) if arguments else {})} for name, arguments in calls]
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(text) if text else {}
    except ValueError:
        return content  # not JSON: the contract check will say so
    if not isinstance(parsed, dict):
        return content
    parsed["actions"] = list(parsed.get("actions") or []) + actions
    return json.dumps(parsed, ensure_ascii=False)


def configured() -> bool:
    return bool(os.environ.get("OPENAI_BASE_URL"))
