"""The lab: a cwa-messages/v1 or cwa-message-blocks/v1 payload becomes an OpenAI-compatible chat request, with no text
of the adapter's own. Write the four functions until `CWA_W9C_IMPL=labs uv run pytest` passes.

texts_of(payload) -> list[str]
    Every text the renderer emitted, in order: each system entry's text, each tool entry parsed and re-serialised as
    canonical JSON (sort_keys, no spaces; a tool entry is an object, so compare it as one), then each message's content, where a blocks message's content is its blocks' texts joined with nothing between (the renderer already
    put the newlines in). This is the "what the model reads" side of the hash comparison.

to_request(payload, model, reserved_output) -> dict
    {"model", "messages", "max_tokens"} and, when the payload has tools, "tools". Every system entry becomes one
    {"role": "system", "content": text} message, in order; then the payload's messages with their role and content
    (blocks joined as above); max_tokens is the route's reserved_output, because the payload was fitted to the input
    budget that remains after it (R-16); each tool entry's text is a JSON tool specification and becomes
    {"type": "function", "function": <that object>}. Nothing else: no preamble, no suffix, no reformatting (§1).

texts_of_request(request) -> list[str]
    The request's texts in the same order as texts_of(): system contents, each tool's function object as canonical
    JSON (sort_keys, no spaces), then the remaining messages' contents. The test hashes both lists.

snippet(request) -> str
    The Python SDK call with the request object inline, so a reader can see that what is sent is what was assembled.

to_anthropic_request() is given in solution/ as reading: the same payload for another API, with a cache breakpoint
placed on a block boundary as structure that adds no text.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def texts_of(payload: bytes) -> list[str]:
    raise NotImplementedError("labs/provider.py: texts_of")


def texts_of_request(request: dict[str, Any]) -> list[str]:
    raise NotImplementedError("labs/provider.py: texts_of_request")


def to_request(payload: bytes, model: str, reserved_output: int) -> dict[str, Any]:
    raise NotImplementedError("labs/provider.py: to_request")


def digest(texts: list[str]) -> str:
    return hashlib.sha256("\x1e".join(texts).encode("utf-8")).hexdigest()


def snippet(request: dict[str, Any]) -> str:
    raise NotImplementedError("labs/provider.py: snippet")
