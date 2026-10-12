# Using an OpenAI-compatible endpoint

Every live path in these workshops speaks the OpenAI chat-completions protocol, because one protocol covers a local Ollama, vLLM, omlx, LM Studio or llama.cpp server as well as hosted gateways such as Groq and OpenRouter. The assembler renders a `cwa-messages/v1` payload; the lab's provider adapter maps its `system`, `tools` and `messages` members onto a chat-completions request and adds no text of its own, so the token count and hash in the trace still describe what the model reads (spec §1, R-16).

## Configuration

`.env` at the repository root, copied from `.env.example`:

| Variable | Meaning | Example |
| --- | --- | --- |
| `OPENAI_BASE_URL` | the endpoint, including `/v1` | `http://localhost:11434/v1` |
| `OPENAI_API_KEY` | whatever the server expects; local servers accept any string | `ollama` |
| `CWA_WORKSHOP_MODEL` | the model name the server lists | `gpt-oss:20b` |
| `CWA_WORKSHOP_REASONING_EFFORT` | `low` for reasoning models, else unset | `low` |
| `CWA_WORKSHOP_EXTRA_BODY` | server-specific request members as JSON, sent as extra body fields | `{"chat_template_kwargs": {"enable_thinking": false}}` |

With `OPENAI_BASE_URL` unset, labs print the request they would have sent and stop.

## Local servers

- **Ollama**: `ollama pull gpt-oss:20b`, then `OPENAI_BASE_URL=http://localhost:11434/v1`.
- **vLLM**: `vllm serve <model>`, then `OPENAI_BASE_URL=http://localhost:8000/v1`.
- **LM Studio**: start the server from the Developer tab; default `http://localhost:1234/v1`.
- **llama.cpp**: `llama-server -m <gguf>`; default `http://localhost:8080/v1`.

## Four things that bite

1. **Reasoning models spend the output budget thinking.** The route's `reserved_output` becomes the request's `max_tokens`. A reasoning model that thinks for all of it returns an empty answer. Set `CWA_WORKSHOP_REASONING_EFFORT=low`; the examples and the demo found this necessary with gpt-oss. Qwen3 models take `enable_thinking` in `chat_template_kwargs` instead: set `CWA_WORKSHOP_EXTRA_BODY` to `{"chat_template_kwargs": {"enable_thinking": false}}`. omlx honours it (a one-line answer went from about 130 completion tokens of thinking to 6); vLLM does too; a server that does not know the member ignores or rejects it, so check yours before a live suite.
2. **The estimate tokenizer is not the model's tokenizer.** Labs count with `estimate-utf8/v1` and a `budget.margin_percent`. W4 measures the real error for your model and sets the margin from it. Until then, keep the default margin.
3. **Tools go to the API as definitions; a native call is folded into the contract.** The capstones' contracts make a tool call a JSON `actions` entry the guards read. The live drafters send the offered tools as the API's tool definitions so the model sees their schemas, and leave `tool_choice` to the model: omlx shows the model nothing when it is `"none"`, and both models then invented argument names. A native tool call in the reply is folded into the contract's `actions`, so the guards see it either way; the content must still be the contract's JSON. The action guard validates arguments against the schema and says exactly what was wrong.
4. **Fenced JSON is still JSON.** gpt-oss-20b wraps its answer in a Markdown code fence. The orchestrators strip a fence before parsing the contract; that is reading the draft, not patching the payload.

## What a live run showed

On 2026-10-11, with omlx serving `gpt-oss-20b-MXFP4-Q8` on an Apple-silicon laptop, the capstone suites passed most positive cases and no suite entirely, so no profile was promoted from that run. `Qwen3.6-35B-A3B-8bit` on the same server, with thinking off and the tools visible, passed C1 and C3 completely, and their profiles are promoted from those reports. Each kit's README records its result. The cases that script a bad draft to exercise a guard are marked `scripted_only` in their `expect.json` and skipped live, since a model is not asked to misbehave; the scripted suite still runs them. The failures that remain are the model's: a stage chosen more cautiously than the expectation allows, an argument renamed against the tool's schema, a tool not called when the instruction asked for it. They are the kind of finding the gate exists to produce, and the evidence a team weighs before promoting a profile for that model.

## Anthropic

The same payload maps onto the Messages API with `system` as a list of text blocks, `tools` as tool definitions and `max_tokens` from `reserved_output`; a cache breakpoint is a `cache_control` marker on a block and adds no text. [anthropic.md](anthropic.md) has the mapping, the two differences that bite, and the configuration.
