# The four assemblers, and where they differ for these workshops

The labs are Python and run the reference assembler. Four implementations pass the same published corpus (65 cases, 25 rejections at specification commit `c252494`), so what a lab shows about a trace, a payload or a refusal holds in every language. This page is the call-out the plan promised: what changes when the application is TypeScript, Go or Rust, module by module, and what never changes.

## What never changes

- **The record.** Snapshot, trace and payload are the published JSON shapes. A snapshot frozen by a Go application assembles to the same bytes under the Python assembler; W9 module D proves it on fullsend's committed scenarios, and the demo's four-way agreement proves it on any snapshot.
- **The outcomes.** Assembled, refused with a trace and no payload, rejected before assembly with problems and no trace, or stopped for a component the implementation does not provide. Every port names them differently and means the same thing.
- **The components.** Every port provides the required tokenizers `fixture-whitespace/v1` and `estimate-utf8/v1` and the required renderers `fixture-xml/v1` and `cwa-messages/v1`, and all four also provide the optional `cwa-message-blocks/v1`. An application tokenizer goes in under an id of its own; a published id is refused before assembly in every port (R-16). No port takes an application renderer.
- **The adapter protocol** (W9 module B): snapshot on stdin; exit 0 with `{payload, trace}`, exit 2 rejected, exit 3 "`<component> <id> is not provided`". The demo and the viability benchmark drive all four through it.

## The four, side by side

| | Python | TypeScript | Go | Rust |
| --- | --- | --- | --- | --- |
| Package | `contextwindowarchitecture-assembler` (git, tag `draft-release`) | `@contextwindowarchitecture/assembler` (pnpm) | `github.com/contextwindowarchitecture/assembler-go` | `contextwindowarchitecture-assembler` (git) |
| Toolchain | Python 3.12+, uv | Node 22+, pnpm, ESM only | Go 1.26+ | Rust 1.80+ |
| Entry point | `assemble(Snapshot.from_json(doc, tokenizers=...))` | `assemble(snapshot, options?)` | `Assemble(snapshotJSON, Options{})` | `assemble(&bytes)`, `assemble_with(&bytes, &options)` |
| Input | a parsed document | a parsed object | JSON bytes | JSON bytes, so the I-JSON checks see the text as written |
| Rejected | `SnapshotError(problems)` | `SnapshotRejectedError` with `problems`; `checkSnapshot()` checks without assembling | `SnapshotRejectedError` | `Error::Rejected(problems)` |
| Unsupported component | `UnsupportedComponentError` (`component`, `id`) | `UnsupportedComponentError` | `UnsupportedComponentError` | `Error::Unsupported(lines)` |
| Published id misused | `ValueError` before assembly | `PublishedTokenizerIdError` with `ids` | an error, no payload, no trace | `Error::PublishedId` |
| Refused | `result.payload is None`, `trace.refused` | `payload === null` | nil `Payload` | `payload: None` |
| Own tokenizer | `tokenizers={id: obj}` on `from_json` / `freeze` | `options.tokenizers` | `Options.Tokenizers` | `Options::new().tokenizer(id, fn)` |
| Own renderer | yes, under an unpublished id (`renderers=`) | no | no | no |
| Timings | only when you lend `assemble()` a clock | always, in milliseconds | always | always (`admission_ms`, `resolution_ms`, `fitting_ms`, `total_ms`) |
| Conformance run | the committed report, checked by a test | `pnpm run conformance` | `scripts/conformance.py --command <adapter>` | `cargo run --release --example conformance` |
| Adapter for W9b's harness | `assembler-demo/adapters/python_adapter.py` | `assembler-demo/adapters/typescript_adapter.mjs` | `go build ./cmd/adapter` | `cargo build --release --example adapter` |

The Python port is the only one that accepts a renderer of the application's own; the other three take the published three and nothing else. No published case covers an application renderer, and a conformant application renders with one the cases cover, so the labs never use one.

## Module by module

| Module | In another language |
| --- | --- |
| W1, W2, W4, W6, W7 | Nothing changes: these read traces and write producers, and both are JSON. A producer written in Go emits the same batch. |
| W3a | Install the port for the application's language instead of the Python package; the migration's seams (freeze, assemble, hand the payload over unchanged, guards outside the model) are the same calls under the names in the table above. |
| W3b | The seams named are Python frameworks. In TypeScript the seam is the Vercel AI SDK's `streamText({ system, messages, tools })`, with `system` and `messages` from the assembler, and `@contextwindowarchitecture/assembler` in the route module. |
| W5 | The capability policy and the guard are application code; the MCP SDKs differ by language, the grant's shape does not. |
| W8 | The kata is a repair of the Python reference. The other three ports have the same discipline: an `AGENTS.md` that forbids reading another port's code and routes specification gaps to the specification repository, a committed conformance report that a test fails when it goes stale, and the vendored contract under `vendor/cwa/` with a lock. A kata on another port would be built the same way from its checkout at its pin. |
| W9a | The adapter pattern (native output to items, provenance from the tool's own identifiers, suppressed entries reported) is language-neutral; the retriever, memory and MCP libraries are not. |
| W9b | The module's harness drives any of the four through the protocol; the table above has each port's adapter command. The four-way agreement is the check that matters when a port disagrees. |
| W9c | The provider adapter adds no text in any language. `assembler-demo/src/provider/` has the OpenAI-compatible and Anthropic mappings in JavaScript; fullsend's `briefing/handoff.go` is the same mapping onto an agent runtime in Go. |
| W9d | The worked example is Go (`integrations/fullsend`, assembler-go); the module ports its producers to Python and proves the port by digest, which is how a second language joins an integration. |
| W10, W11 | The specification's checker and generators are Python; the viability benchmark's Domain 1 runs all four ports as black boxes and reports them side by side. |
| Capstones | A team may build a capstone in TypeScript, Go or Rust against the same data and policy files: the gate's checks are over the record (snapshots, traces, outcomes), which is language-neutral, and a port of `app.py` is a day's work on top of the day. |

## Cost notes that differ

Every port renders and counts the whole payload for each fit test, so shedding many items is proportional to the number of reductions times the payload's size. The ports report different constants (about a third of a second to shed 498 of 500 passages in TypeScript, about 0.2 s for 499 of 500 in a Rust release build); the advice is the same in all four: send no more passages than the route's budget can use, and bound slots with `max_per_source` or `max_tokens`. `cwa-message-blocks/v1` counts each entry on its own, so with `estimate-utf8/v1`, which rounds each text up, the same items can count more than under `cwa-messages/v1` and fewer fit; W6's cache measure and C3's profile use it knowingly.

## Keeping this page honest

The figures and names here are from the four checkouts at their `draft-release` tags and the specification's `implementations/` reports at `c252494`. When a pin moves, re-read each port's README and conformance report and update the table in the same commit as the pin.
