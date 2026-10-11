# W9 module C. The provider adapter

Half a day, self-paced, model-free. You leave able to add a provider without touching assembly, and able to prove by hash that what was sent is what was assembled.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` installs the reference assembler and the OpenAI SDK. Sending is optional and needs an endpoint.
- W1. W3a helps: its `provider.py` is a smaller version of this lab.
- Open [worksheet.md](worksheet.md) beside this file.

Conference cut (60 minutes): part 1 and the lab's first two tests.

## The last mile

The assembler renders an intermediate representation. `cwa-messages/v1` is `{system, tools, messages}`: governance placed as `system` or `tools` becomes entries in those channels, everything else is one user message whose text holds every other item in placement order, prior turns included as a transcript. `cwa-message-blocks/v1` is the same request with the user message's content as one `{id, text}` entry per item. A provider adapter maps that onto a vendor's API and adds nothing: no preamble, no suffix, no reformatting (§1). Request structure the renderer leaves to it, a cache breakpoint, a cache key, a lifetime, is allowed because it adds no text, so the token count and the hash in the trace still describe what the model reads.

```sh
uv sync
uv run payloads.py
```

The specification's own example snapshot, rendered under both renderers, and refused when the budget is cut to 90: two payloads to adapt and one case where there is nothing to adapt.

## Part 1. Read the reference (20 minutes)

Read [solution/provider.py](solution/provider.py) for the OpenAI-compatible mapping and for `to_anthropic_request()`, the same payload for the Messages API with a cache breakpoint placed on a block boundary. Then:

```sh
uv run send.py
uv run send.py --blocks
```

Each prints the exact outbound request, then three hashes: the payload's from the trace, the hash of the texts the model reads, and the hash of the texts the request carries. The last two are equal, which is the whole point. With `OPENAI_BASE_URL` set it also sends.

**Checkpoint 1.** The worksheet's part 1 lines: how each channel of the IR maps, and what the two equal hashes prove.

## The lab. Write the adapter (60 minutes)

Open [labs/provider.py](labs/provider.py): four functions, the docstring is the specification.

```sh
CWA_W9C_IMPL=labs uv run pytest
uv run send.py --impl labs --blocks
uv run send.py --impl labs --snippet
```

The tests check what adapters get wrong: a system entry merged into the user turn, a prior turn promoted to an assistant message, a tool specification rewritten, `max_tokens` set to a constant rather than the route's `reserved_output`, blocks joined with a separator the renderer did not emit, and any text added anywhere. One test is a refusal, where there is no payload and so no request; the application sends nothing (R-17).

**Checkpoint 2.** The two hashes equal under both renderers through your adapter, and the SDK snippet for one request.

## Part 3. Breakpoints as structure (30 minutes)

Run the Anthropic mapping in the solution with and without a breakpoint and diff the texts: identical. The breakpoint is a `cache_control` marker on one block; it changes what the provider caches and nothing the model reads. Then read W6's cache-reuse measurement again: that is the renderer's half of the bargain, a stable prefix at block boundaries; this is the adapter's half, marking the boundary without adding a byte.

**Checkpoint 3.** The block you placed the breakpoint after and why that one.

## After this module

- Add a provider your team uses, keep the two hashes equal, and commit the snippet generator with it.
- Module D studies a host, fullsend, where the adapter's other direction matters: the host's permissions become authority.

## Covers

R-7 (roles), R-16 (count and margin), R-17 (nothing sent on a refusal), §1 (the handoff).

## Files

- `labs/provider.py`: the lab. `solution/provider.py`: finished, with the Anthropic mapping as reading. `impl.py`: the `CWA_W9C_IMPL` switch.
- `payloads.py`: the example snapshot under both renderers and refused. `send.py`: adapt, hash, optionally send.
- `tests/`: the handoff tests.
