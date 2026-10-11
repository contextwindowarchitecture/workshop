# Using the Anthropic Messages API

The workshops' live paths speak the OpenAI chat-completions protocol by default ([openai-compatible.md](openai-compatible.md)). The same assembled payload maps onto the Anthropic Messages API without a model-specific change anywhere in assembly, because a provider adapter adds no text: it moves the renderer's channels into the vendor's request shape and nothing else (spec §1, R-7, R-16). This page is the mapping, the two things the Messages API does differently, and where the code lives.

## The mapping

A `cwa-messages/v1` payload is `{system, tools, messages}`. For the Messages API:

| Payload | Request | Note |
| --- | --- | --- |
| each `system` entry, in order | one block in the `system` list: `{"type": "text", "text": ...}` | the API takes `system` as a list of blocks, so the entries stay separate; no separator is added |
| each `tools` entry | one tool definition `{"name", "description", "input_schema"}` from the entry's JSON text | the payload's tool text is already a specification; the adapter parses it and renames nothing |
| the one user message, string content | `{"role": "user", "content": text}` | `cwa-messages/v1` renders exactly one user message; the history the route admitted is inside it |
| the one user message, block content (`cwa-message-blocks/v1`) | `{"role": "user", "content": [{"type": "text", "text": ...}, ...]}`, one block per item | this is where a cache breakpoint can sit |
| the route's `reserved_output` | `max_tokens` | required by the API; the payload was fitted to the input budget that remains after it (R-16) |

The reference is `to_anthropic_request()` in [09-adapters/c-provider/solution/provider.py](../../09-adapters/c-provider/solution/provider.py). The demo's `assembler-demo/src/provider/anthropic.mjs` is the same mapping in JavaScript, with credential discovery and a thinking option.

```python
import anthropic
from solution.provider import to_anthropic_request   # 09-adapters/c-provider

request = to_anthropic_request(result.payload, model="claude-sonnet-5-5", reserved_output=context.reserved_output())
client = anthropic.Anthropic()                        # ANTHROPIC_API_KEY, or ANTHROPIC_BASE_URL for a compatible server
message = client.messages.create(**request)
text = "".join(block.text for block in message.content if block.type == "text")
```

Proof, as in W9 module C: the texts in the request equal the texts in the payload, so the token count and the hash the trace recorded still describe what the model reads. The module's tests compare them.

## Two things the API does differently

1. **Prompt caching is explicit.** The API caches an unchanged prefix up to a `cache_control: {"type": "ephemeral"}` marker on a block. The marker is structure, not text: W9 module C places one on a block boundary of the user message (the last stable item, under a cache-first profile) and shows the texts unchanged with and without it. Cached prefixes have a minimum length that varies by model, so a short payload is never cached whatever is marked; the `system` list and the tools count toward the prefix. W6's reuse measurement is the renderer's half of the bargain, a stable prefix at block boundaries; the marker is the adapter's half.
2. **Extended thinking spends the output budget.** As with reasoning models on OpenAI-compatible servers, a model that thinks for all of `max_tokens` returns no text. Where thinking is enabled, size `reserved_output` for the route to cover it, and read every text block of the reply rather than the first. The demo's adapter enables adaptive thinking for the hosted API and turns it off for a custom base URL, which may not know the parameter.

## Configuration

| Variable | Meaning |
| --- | --- |
| `ANTHROPIC_API_KEY` | the key; the SDK reads it from the environment |
| `ANTHROPIC_BASE_URL` | optional: an Anthropic-compatible server, for example a local one; thinking and beta features off unless the server is known to take them |
| `CWA_WORKSHOP_MODEL` | the model id, as for the OpenAI-compatible path |

Nothing in the workshops' model-free paths changes: the committed snapshots, traces and payloads are the same whatever provider the live path uses, which is the point of the handoff rule.
