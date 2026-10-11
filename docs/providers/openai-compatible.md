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

With `OPENAI_BASE_URL` unset, labs print the request they would have sent and stop.

## Local servers

- **Ollama**: `ollama pull gpt-oss:20b`, then `OPENAI_BASE_URL=http://localhost:11434/v1`.
- **vLLM**: `vllm serve <model>`, then `OPENAI_BASE_URL=http://localhost:8000/v1`.
- **LM Studio**: start the server from the Developer tab; default `http://localhost:1234/v1`.
- **llama.cpp**: `llama-server -m <gguf>`; default `http://localhost:8080/v1`.

## Two things that bite

1. **Reasoning models spend the output budget thinking.** The route's `reserved_output` becomes the request's `max_tokens`. A reasoning model that thinks for all of it returns an empty answer. Set `CWA_WORKSHOP_REASONING_EFFORT=low`; the examples and the demo found this necessary with gpt-oss.
2. **The estimate tokenizer is not the model's tokenizer.** Labs count with `estimate-utf8/v1` and a `budget.margin_percent`. W4 measures the real error for your model and sets the margin from it. Until then, keep the default margin.

## Anthropic

Not yet written. The `cwa-messages/v1` shape maps onto the Messages API in the same way, with `system` as the system parameter and `tools` as the tool list; `assembler-demo/src/provider/anthropic.mjs` is a working adapter to read in the meantime.
