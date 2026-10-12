"""The last mile: a cwa-messages/v1 payload becomes an OpenAI-compatible chat request, with no text of this module's own.

request_for() is pure and tested: the system entries become system messages, the payload's messages follow, and
max_tokens is the route's reserved_output. send() posts it when OPENAI_BASE_URL is set and prints it otherwise. The
before app calls the same send() with a request it built by hand; that is the only thing the two apps share here.
"""

from __future__ import annotations

import json
import os
from typing import Any


def request_for(payload: bytes, model: str, reserved_output: int) -> dict[str, Any]:
    """The chat-completions request body for an assembled payload. Adds nothing the renderer did not emit (§1)."""
    rendered = json.loads(payload)
    messages = [{"role": "system", "content": entry["text"]} for entry in rendered.get("system", [])]
    for message in rendered["messages"]:
        content = message["content"]
        if isinstance(content, list):  # cwa-message-blocks/v1: one entry per item
            content = "".join(block["text"] for block in content)
        messages.append({"role": message["role"], "content": content})
    request: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": reserved_output}
    if rendered.get("tools"):
        request["tools"] = [{"type": "function", "function": tool} for tool in rendered["tools"]]
    return request


def configured() -> bool:
    return bool(os.environ.get("OPENAI_BASE_URL"))


def send(request: dict[str, Any]) -> str | None:
    """Post the request to the configured endpoint, or print it and return None when none is configured."""
    if not configured():
        for message in request["messages"]:
            print(f"\n-- {message['role']} --\n{message['content']}")
        print(f"\n(no OPENAI_BASE_URL set: printed instead of sent; max_tokens {request['max_tokens']}, model {request['model']})")
        return None
    from openai import OpenAI

    client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ.get("OPENAI_API_KEY", "none"))
    extra = {}
    if os.environ.get("CWA_WORKSHOP_REASONING_EFFORT"):
        extra["reasoning_effort"] = os.environ["CWA_WORKSHOP_REASONING_EFFORT"]
    if os.environ.get("CWA_WORKSHOP_EXTRA_BODY"):  # server-specific members, e.g. {"chat_template_kwargs": {"enable_thinking": false}}
        extra["extra_body"] = json.loads(os.environ["CWA_WORKSHOP_EXTRA_BODY"])
    response = client.chat.completions.create(**request, **extra)
    return response.choices[0].message.content or ""


def model() -> str:
    return os.environ.get("CWA_WORKSHOP_MODEL", "local-model")
