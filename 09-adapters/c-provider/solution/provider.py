"""Lab solved: cwa-messages/v1 and cwa-message-blocks/v1 to an OpenAI-compatible chat request, with no text of its own."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def texts_of(payload: bytes) -> list[str]:
    """Every text the renderer emitted, in order: the system entries, the tool specifications, the user content."""
    ir = json.loads(payload)
    out = [e["text"] for e in ir.get("system", [])]
    out += [_canonical(json.loads(e["text"])) for e in ir.get("tools", [])]  # a tool entry is a JSON object; compare it as one
    for message in ir["messages"]:
        content = message["content"]
        out.append(content if isinstance(content, str) else "".join(block["text"] for block in content))
    return out


def texts_of_request(request: dict[str, Any]) -> list[str]:
    """Every text the request carries, in the same order, so the two lists can be hashed and compared."""
    out = [m["content"] for m in request["messages"] if m["role"] == "system"]
    out += [_canonical(t["function"]) for t in request.get("tools", [])]
    out += [m["content"] for m in request["messages"] if m["role"] != "system"]
    return out


def to_request(payload: bytes, model: str, reserved_output: int) -> dict[str, Any]:
    ir = json.loads(payload)
    messages = [{"role": "system", "content": entry["text"]} for entry in ir.get("system", [])]
    for message in ir["messages"]:
        content = message["content"]
        if isinstance(content, list):
            content = "".join(block["text"] for block in content)  # blocks join with nothing between: the renderer put the newlines in
        messages.append({"role": message["role"], "content": content})
    request: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": reserved_output}
    if ir.get("tools"):
        request["tools"] = [{"type": "function", "function": json.loads(entry["text"], object_pairs_hook=dict)} for entry in ir["tools"]]
    return request


def to_anthropic_request(payload: bytes, model: str, reserved_output: int, breakpoint_after: str | None = None) -> dict[str, Any]:
    """The same payload for the Messages API. A cache breakpoint is structure, not text: cache_control on a block
    boundary adds nothing the model reads, so the count and hash the trace recorded still describe the request (§1)."""
    ir = json.loads(payload)
    request: dict[str, Any] = {"model": model, "max_tokens": reserved_output}
    if ir.get("system"):
        request["system"] = [{"type": "text", "text": e["text"]} for e in ir["system"]]
    if ir.get("tools"):
        request["tools"] = [json.loads(e["text"]) for e in ir["tools"]]
    content = ir["messages"][0]["content"]
    if isinstance(content, str):
        request["messages"] = [{"role": "user", "content": content}]
    else:
        blocks = [{"type": "text", "text": b["text"], **({"cache_control": {"type": "ephemeral"}} if b["id"] == breakpoint_after else {})} for b in content]
        request["messages"] = [{"role": "user", "content": blocks}]
    return request


def digest(texts: list[str]) -> str:
    return hashlib.sha256("\x1e".join(texts).encode("utf-8")).hexdigest()


def snippet(request: dict[str, Any]) -> str:
    """The copy-pasteable Python SDK call. The object in it is the request, built by the same code."""
    body = json.dumps(request, indent=4, ensure_ascii=False)
    return ("from openai import OpenAI\n\nclient = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)\n"
            f"response = client.chat.completions.create(**{body})\nprint(response.choices[0].message.content)\n")
