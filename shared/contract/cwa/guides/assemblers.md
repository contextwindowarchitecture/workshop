# CWA for assemblers

> How to use a Context Window Architecture (CWA) assembler, or build one: the component that turns a frozen snapshot into a rendered payload and a trace. Four implementations exist, in Python, TypeScript, Go and Rust, built independently from the published contract, and none is released. Rules are cited by their permanent number (R-n) and are normative in [SPEC.md](../SPEC.md), which the Spec page, https://contextwindowarchitecture.io/spec.html, renders; conformance/README.md is normative wherever they leave an ordering, tie-break, boundary or algorithm step open (R-21). Its tables of refusal codes and requirement scope and its list of implementations are written from the contract files and [implementations/index.json](../implementations/index.json) by `python3 conformance/check.py --write`; the copy on the site, https://contextwindowarchitecture.io/llms-assemblers.txt, also counts each implementation's report against the published cases.

## What an assembler does

An assembler takes one snapshot, valid against schema/snapshot.schema.json: `assembly_time`, `scope`, `budget`, `profile`, `route_policy`, `tokenizer`, `renderer`, `batches` (each `{ producer: { id, kind }, items, excluded }`), `conflicts`, and, when the route admits tools, the capability grant `capabilities`. The application builds it: it runs the producers, authenticates each one, reads the clock once and freezes everything that can affect the payload (R-23). Assembly reads nothing else: no model calls (R-18), no network, no files, no ambient clock.

Every call ends in exactly one of these:

- Assembled: the payload bytes and a trace with `refused: { bool: false, reason: null }` and `result: { input_tokens, hash }`, where `hash` is the lowercase SHA-256 of the exact payload bytes (R-21).
- Refused: no payload, and a trace with `refused.bool: true`, a reason code, `result: null`, `included: []` and `compressed: []`, keeping every exclusion, conflict record and filled default recorded before the refusal (R-17). Refusals are outcomes of valid snapshots.
- Rejected: the snapshot fails its schemas or a snapshot check, so there is no payload and no trace (R-17). No reason code names a rejection; the implementation lists the problems in its own words.
- Stopped: the application supplied a tokenizer under a published tokenizer's ID, or a renderer under a published renderer's ID. There is no payload and no trace (R-16).
- Unsupported: the snapshot names a tokenizer or renderer the implementation does not provide. That is no problem with the snapshot, so it is not a rejection, and there is no payload and no trace.

Identical snapshots give identical payload bytes and hash, or the same refusal, in any process, locale or language (R-23). Only `trace_id`, `timings` and the free-text `recovery.detail` may differ between runs.

## The pipeline

The order every implementation follows, from conformance/README.md:

1. Validate. Check the snapshot against its schemas, I-JSON (no unpaired surrogates, every number a finite double) and the Snapshot checks: one batch per producer, conflict groups that name real candidates or producer exclusions with at most one group per item, producer exclusions whose `duplicate_of` or `superseded_by` names a candidate in the same batch, and a profile whose `spec` is `cwa/draft`, whose route and route-policy version match the route policy's, that places the required slots, and that the renderer can realize. Reject on any failure (R-17).
2. Admit. Check every candidate, filling and tracing the policy defaults it omits (R-3), and exclude a failure with the earliest applicable code in contract/reasons.json order (R-21). Merge the producers' own exclusion rows into the trace (R-9). Placement is the last admission check (R-20).
3. Resolve the declared conflict groups, and only those: instruction groups by authority and the peers' `conflict_policy`, fact groups by the route's precedence of authenticated producers, escalating where neither decides (R-6, R-11).
4. Supersede stale observations in the slots that set `supersede: "source"` (R-25).
5. Deduplicate exact bodies in the slots that set `dedupe: "exact"` (R-24).
6. Cap each producer and source at `max_per_source` in the slots that set it (R-26).
7. Check the refusals and fit. Refuse for a missing required slot, an unplaced protected item, an unresolved conflict or protected content that cannot fit, in that order; then enforce item caps, slot caps and budget pressure in tier order with slot floors, and refuse after fitting when a floor withheld the fit or too little evidence is left (R-4, R-12, R-16, R-17, R-20).
8. Render with the snapshot's renderer, count with its tokenizer, and hash the payload bytes.
9. Trace: every decision above, in the array orders conformance/README.md fixes (R-21, R-22).

Refusal codes, in the order the first that holds is recorded (contract/reasons.json):

<!-- generated:refusals -->

| Code | Rule | When |
| --- | --- | --- |
| `required_slot_missing` | R-4 | governance.instructions or interaction.query, or governance.output_contract on a parser route, has no admitted item. |
| `protected_slot_unplaced` | R-20 | An admitted protected item's slot has no placement in the profile. The profile must not omit protected content, so the assembler refuses rather than drop it. |
| `conflict_unresolved` | R-11 | A declared conflict group has no unique supported resolution, and route policy says to refuse or request context. The trace records recovery.action request_context when every such group asked for context. |
| `protected_content_over_budget` | R-17 | The payload rendered from protected content alone does not fit budget.input, charged with any margin_percent, or protected items exceed their slot's max_tokens, or a protected item exceeds its own token_budget. The assembler refuses rather than truncating. |
| `slot_floor_over_budget` | R-17 | The payload does not fit budget.input without shedding a slot below the route's min_tokens. The assembler refuses rather than break the floor. |
| `evidence_required` | R-12 | The route requires evidence and too little survived admission and fitting. The trace records recovery.action. |

<!-- /generated:refusals -->

## The conformance claim

A conformant assembler meets every MUST an assembler can meet by itself, provides every tokenizer and renderer that conformance/README.md requires, and can emit its trace as JSON with the fields R-21 lists (spec §1). Because a model accepts any payload, a wrong decision fails silently, so the claim rests on evidence: a conformance report, valid against schema/conformance_report.schema.json, showing that the assembler passes every published case and rejects every published rejection. It may skip only a case that uses an optional tokenizer or renderer it does not provide; today all four published components are required, so it may skip none. Schema validation alone is not conformance (R-21).

A case passes when the payload matches `expected.payload.txt` byte for byte, or there is no payload where that file is absent, and the trace matches `expected.trace.json` field for field once `trace_id`, `timings` and `recovery.detail` are removed. Array order in the trace is part of the expectation. A rejection case passes when the snapshot is rejected before assembly, with no payload and no trace.

## Requirement scope

What an assembler can check of each requirement (contract/assembler-scope.json). Assembler rows are fully testable in assembly. Boundary rows are checked where the snapshot and its items are handed over, and the rest of the obligation sits with producers or the application. Application rows cannot be observed during assembly.

<!-- generated:scope -->

| Rule | Summary | Scope | What an assembler checks |
| --- | --- | --- | --- |
| R-1 | One slot and one authority role per item | assembler | Admission checks each item's slot and authority. |
| R-2 | Required fields and canonical JSON shape | assembler | Schema validation with format checking; timestamps compared at full precision. |
| R-3 | Declared policy defaults, filled and traced | assembler | Fills slot defaults and versioned route overrides, records defaults_filled, and applies the four slot-level eligibility rules as the complete predicate. |
| R-4 | Slots that are never omitted | boundary | Refuses with required_slot_missing. Declaring parser: true on every route whose response a parser consumes is the application's. |
| R-5 | Rule zero: enforce outside the model | application | Application guards enforce invariants. Nothing observable in assembly can prove it. |
| R-6 | Separate instruction authority from factual precedence | assembler | Classifies each declared group as instruction or fact and resolves it by authority or route policy; only governing and user items are instruction peers, and trust and the injection marker never change that. |
| R-7 | No slot overrides platform roles; no authority from wording | assembler | Only governance takes the system and tool roles, the query is the only live user turn, history renders as a transcript in the order turns were said, and item bodies are escaped inside xml: wrappers; cwa-messages/v1 hands system and tools text over unescaped. |
| R-8 | State is application-written and current | boundary | Checks producer kind and state age. Writing state stays with the application. |
| R-9 | Memory lifetime and producer exclusion reporting | boundary | Excludes expired and revoked memory and merges producer exclusions. Reporting them is the producer's duty. |
| R-10 | User and fetched content is marked, never elevated, kept out of governance | boundary | Checks the marker in the five slots that require it, keeps unverified or marked items out of governance, and renders every body whole. Marking user-controlled and fetched content is the producer's duty, and delimiting material pasted into a body is the application's job. |
| R-11 | Explicit conflict groups and traceable resolution | boundary | Resolves the groups it is given. It cannot detect a conflict the application did not declare. |
| R-12 | Never answer from nothing | boundary | Refuses with evidence_required and a recovery action. Retrieving and summarizing before the snapshot is frozen, and freezing a new one for any retry, are the application's. |
| R-13 | Retrievers emit one scored item per chunk, never a blob | boundary | Gates retrieval producers to the evidence slots, requires the slot's authority, a score on every knowledge item and wherever the route sets a threshold, and that a reported near-duplicate names a candidate the producer kept. It cannot tell whether a producer merged chunks or dropped one silently. |
| R-14 | Memory producers suppress and report expired or revoked items | boundary | Re-excludes expired or revoked memory as a backstop. Suppressing and reporting them is the producer's duty. |
| R-15 | Authenticated capability admission; MCP output is evidence | boundary | Checks the authenticated emitter and capability grant. The application authenticates, and tool guards enforce calls. |
| R-16 | Account for rendered tokens; shed in tier order | boundary | Counts rendered tokens and sheds in tier order. Setting budget.input from the model's context limit, with a tokenizer that counts or estimates the model's tokens, is the application's. |
| R-17 | Refused assembly has no rendered payload | assembler | Refused assemblies have no payload, and their traces carry result: null and no included items. Invalid snapshots are rejected before assembly, with no payload and no trace. |
| R-18 | Precomputed variants; no model calls during assembly | boundary | Selects only supplied variants and never calls a model. It cannot verify a variant's fidelity. |
| R-19 | Draft profiles versus evaluated profiles | boundary | Rejects a profile written for another spec. Evaluation and promotion happen outside assembly: the Python assembler's registry hands a deployment only an evaluated profile, which no case covers. |
| R-20 | Profile version and mandatory-slot validation | boundary | Rejects a profile that doesn't place a required slot, and refuses the assembly when admitted protected content has no placement. Raising the version for every change is the application's; the Python assembler's registry pins content by digest, outside assembly and the cases. |
| R-21 | Trace JSON matches the published schema | assembler | Traces are checked against the schema and the reason registry, and must match every published case field for field. |
| R-22 | Provenance, snapshot digest and filled defaults in the trace | assembler | Emits source_version, eligibility, excluded slots, snapshot_digest and defaults_filled, and stage timings when the caller lends a clock. |
| R-23 | Determinism includes the clock and policy snapshot | boundary | Snapshot replay across processes, hash seeds, time zones and locales, with ordering, blank strings, timestamps and the digest pinned for every language. Making every external read and model call before the snapshot is frozen is the application's. |
| R-24 | Route-requested exact deduplication | assembler | Excludes exact duplicate bodies in the slots a route opts in, after conflicts, keeping protected and grouped items. |
| R-25 | Route-requested supersession of stale observations | assembler | Keeps only the latest observation per producer and source in the slots a route opts in, after conflicts, keeping protected and grouped items. |
| R-26 | Route-requested source diversity | assembler | Keeps at most max_per_source items per producer and source in the slots a route opts in, after dedupe, keeping protected and grouped items. |

<!-- /generated:scope -->

## Tokenizers and renderers

Every implementation provides these four, exactly as conformance/README.md defines them, and every published case uses them or the optional renderer after them:

- `fixture-whitespace/v1` counts maximal runs of characters outside the ECMAScript whitespace and line-terminator set. It is a test fixture, not a model tokenizer.
- `estimate-utf8/v1` counts `(UTF-8 bytes + 3)` divided by 4, discarding the remainder: a portable estimate for a model with no local tokenizer, to pair with a `budget.margin_percent` that covers its error.
- `fixture-xml/v1` renders each placed item as `<{tag} id="{id}">`, its escaped body on a line of its own, then `</{tag}>`, in placement order and by id within a placement, except history turns, which go in the order they were said: by freshness, then id (R-7). It supports only `xml:` wraps.
- `cwa-messages/v1` renders a message request, the RFC 8785 serialization of `{ system, tools, messages }`: governance placed with wrap `system` or `tools` becomes those entries, and every `xml:` placement goes into exactly one user message, rendered as `fixture-xml/v1` renders it, with prior turns marked by `speaker` as part of the transcript (R-7). The query is the only live user turn.

`cwa-message-blocks/v1` was published later as optional. It renders the `cwa-messages/v1` request with the user message as one `{id, text}` entry per placed item, so an application can put a provider's cache breakpoint between any two items. Its count sums every entry's text, so an estimating tokenizer can fit fewer items than under `cwa-messages/v1`. An implementation that leaves it out skips the cases that use it, and still stops on an application renderer under its ID (R-16).

The payload *fits* when its count, times `(100 + margin_percent) / 100` rounded up in integer arithmetic, is at most `budget.input`; only that test takes the margin, and caps, floors and traced counts stay unscaled (R-16). An application may count with a tokenizer of its own under an ID no published tokenizer uses; an assembler stops before assembly on an application tokenizer or renderer that takes a published ID (R-16).

## Portability traps

Each is a place where languages disagree. Most have a published case written to catch them, named in parentheses with the README section that settles them; the last two no case can reach, so each implementation tests them itself.

- Strings sort by UTF-16 code units, with a prefix first. Python, Go and Rust compare code points by default, which differs beyond U+FFFF (Ordering; `ordering-astral-ids`).
- "Blank" and the whitespace tokenizer use the ECMAScript whitespace set, spelled out. Python's `\s` and `\S` differ at U+001C to U+001F and U+FEFF (Blank strings; `admission-reasons`).
- The schemas' patterns need ECMAScript regex semantics: `\uXXXX` escapes and the `(?![\s\S])` end anchor. RE2-style engines, such as Go's `regexp`, reject both.
- Assert `format: date-time`: the pattern pins the shape but not the calendar, and `admission-reasons` holds `2026-02-30` as `invalid_structure`. Compare instants at full precision, with a fraction of any length and no leap seconds (Timestamps).
- Read every number as the nearest IEEE 754 double before comparing it, so integers beyond 2^53 may tie, and reject a number outside the double range rather than crash (Numbers; `threshold-beyond-2-53`, `digest-beyond-2-53`, rejection `number-out-of-range`).
- Reject an unpaired surrogate from the raw text. Some JSON parsers, Go's `encoding/json` among them, silently replace it with U+FFFD (rejection `unpaired-surrogate`).
- Serialize with RFC 8785, ECMAScript number formatting included, for the snapshot digest, the order of rows sharing an id, and the `cwa-messages/v1` payload (Snapshot digest). Beyond 2^53 a whole double is written with its shortest round-trip digits padded with zeros, not its exact value (`digest-beyond-2-53`).
- Compare deduplication keys code unit for code unit: no Unicode normalization and no case folding (Deduplication; `dedupe-exact`).
- Every reduction under budget pressure is its own fit test over the whole rendered payload, and an implementation may reach the same decisions faster but never different ones (Fitting).
- Look up tokenizer, renderer and producer IDs as own keys only: a schema-valid snapshot can name `toString` or `__proto__`.
- Sort every output by its stated keys; never iterate a hash map into output.

## Using an implementation

None is released, so work from a checkout. Each publishes a conformance report, and the Assembler page counts it against the published cases as they are now: a case published or changed since the run does not count as passing (conformance/README.md, Reporting results).

<!-- generated:implementations -->

| Language | Package | Repository |
| --- | --- | --- |
| Python | `contextwindowarchitecture-assembler` 0.0.1 | https://github.com/contextwindowarchitecture/assembler-python |
| TypeScript | `@contextwindowarchitecture/assembler` 0.0.1 | https://github.com/contextwindowarchitecture/assembler-typescript |
| Go | `github.com/contextwindowarchitecture/assembler-go` 0.0.1 | https://github.com/contextwindowarchitecture/assembler-go |
| Rust | `contextwindowarchitecture-assembler` 0.0.1 | https://github.com/contextwindowarchitecture/assembler-rust |

<!-- /generated:implementations -->

Python, module `cwa` (Python 3.11 or newer; `uv sync` in the checkout):

```python
import json
from cwa import Snapshot, SnapshotError, UnsupportedComponentError, assemble

snapshot = Snapshot.from_json(json.load(open("snapshot.json")))  # SnapshotError rejects; .problems says why
result = assemble(snapshot)  # pure: no I/O, clock or model
result.payload    # bytes, or None when refused
result.trace      # dict matching trace.schema.json
result.refused    # trace["refused"]["bool"]
snapshot.digest() # context.snapshot_digest, the replay key
```

Pass your own tokenizers as `Snapshot.from_json(document, tokenizers={tok.id: tok})`, where any object with an `id` and a `count(text)` will do. A registry in `cwa.registry` pins profiles and route policies by digest and returns only evaluated profiles in deployment mode.

TypeScript, package `@contextwindowarchitecture/assembler` (Node.js 22 or newer, ESM; `pnpm install --frozen-lockfile && pnpm run build` in the checkout):

```ts
import { assemble, checkSnapshot, SnapshotRejectedError, UnsupportedComponentError } from '@contextwindowarchitecture/assembler';

const { payload, trace } = assemble(snapshot); // payload: Uint8Array, or null when refused
```

`assemble(snapshot, { tokenizers })` takes your own tokenizers keyed by their IDs; it accepts no renderer of the application's own. `checkSnapshot(snapshot)` lists a snapshot's problems without assembling.

Go, module `github.com/contextwindowarchitecture/assembler-go`, package `assembler` (Go 1.26 or newer):

```go
result, err := assembler.Assemble(snapshotJSON, assembler.Options{})
// err is a SnapshotRejectedError or UnsupportedComponentError before assembly;
// result.Payload is nil when the assembly is refused, and result.Trace holds the trace.
```

`Options.Tokenizers` takes your own tokenizers for one call; there is no option for a renderer.

Rust, crate `contextwindowarchitecture-assembler` (Rust 1.80 or newer; a git dependency on the repository):

```rust
use contextwindowarchitecture_assembler::{assemble, assemble_with, Error, Options};

let assembly = assemble(&snapshot_bytes)?; // Error::Rejected or Error::Unsupported before assembly
// assembly.payload is None when the assembly is refused, and assembly.trace holds the trace.
```

`assemble_with(&snapshot_bytes, &Options::new().tokenizer(id, count))` takes your own tokenizer under an ID no published tokenizer uses; a published ID is `Error::PublishedId`, and there is no option for a renderer. It takes the snapshot's bytes, not parsed JSON, so the I-JSON checks see the text as written.

All four render examples/messages-snapshot.json to examples/messages-payload.json byte for byte, a `cwa-messages/v1` request `conformance/check.py` also derives from that snapshot, and emit examples/messages-trace.json as its trace, `trace_id` aside.

## Building a new implementation

Start from the template, https://github.com/contextwindowarchitecture/assembler-template, and follow its PORTING.md:

1. Name the port with `scripts/init_port.py`, then vendor the contract from a checkout of the specification repository with `scripts/vendor_contract.py --spec ../contextwindowarchitecture`. It copies the schemas, contract data, cases, rejections and registry into `vendor/cwa/`, each file pinned by SHA-256 with the commit in `vendor/cwa.lock.json`.
2. Read conformance/README.md end to end, then contract/requirements.json, then the snapshot and trace schemas, then one case, `fixture-three-slot`, with its snapshot, trace and payload side by side. The requirements say what must happen; the README says how.
3. Build test-first, in this order: strings and instants; canonical JSON and the digest; schemas and snapshot checks (every rejection case); tokenizers and renderers; admission and defaults; conflicts, supersession, deduplication and source diversity; refusals and fitting; the trace and the runner. Unit-test each README section's rules before letting its cases pass, and keep cases the port cannot pass yet in a `PENDING` set that only shrinks.
4. Run the cases through a small adapter: `python3 scripts/conformance.py --command "<adapter>" --name <package> --version <version> --language <Language>`, then `python3 scripts/check_report.py`. The adapter reads one snapshot's raw bytes on stdin and exits 0 with `{"payload": <base64 or null>, "trace": <trace>}` on stdout for an assembly or a refusal, 2 with the problems on stderr for a rejection, and 3 for a tokenizer or renderer it does not provide.
5. Commit the report with every change that alters it. To list the port, import its report into a checkout of the specification repository with `conformance/import_report.py` and open a pull request (conformance/README.md, Reporting results); the Assembler page then counts, per requirement, the cases it passes.

Build from the published contract alone, and never read another implementation's code. Two implementations that both pass every case and still disagree have found a gap in the spec, and the fix is a spec change with a case, made in the specification repository first and vendored after.

## What an assembler does not do

The application meets the MUSTs no component can meet for it (spec §1). It enforces invariants and tool permissions outside the model (R-5, R-15), writes state (R-8), declares conflict groups (R-11), authenticates each producer and binds its identity outside the items (R-15), makes every external read, retrieval and model call before it freezes the snapshot and freezes a new one for any retry (R-12, R-23), sets `parser: true` on every route whose response a downstream parser consumes (R-4), sets `budget.input` to the model's context limit less `budget.reserved_output` (R-16), versions its profiles (R-20) and deploys only evaluated ones (R-19). It renders with a renderer the published cases cover, and declares a tokenizer that reads nothing but the text it counts and counts the model's tokens, or estimates them with a covering margin (R-16, R-23).

It hands the payload to the model with each text in the platform role its renderer assigns, text assigned none in a single user message where the query alone is the live turn, and no text of its own. Request structure the renderer leaves to it, such as a provider's cache breakpoints, cache lifetime or cache key, adds no text, so the count and hash its trace records still describe what the model reads. The roles R-7 has the assembler assign, and the count R-16 has it make, hold for the payload the assembler renders; only this handoff makes them hold for what the model receives.

## Sources

- Conformance README, the algorithm: [conformance/README.md](../conformance/README.md)
- Requirements: [SPEC.md](../SPEC.md) and [contract/requirements.json](../contract/requirements.json)
- Reason codes, in rank order: [contract/reasons.json](../contract/reasons.json)
- Slot defaults: [contract/slot-defaults.json](../contract/slot-defaults.json)
- Snapshot schema: [schema/snapshot.schema.json](../schema/snapshot.schema.json)
- Trace schema: [schema/trace.schema.json](../schema/trace.schema.json)
- Conformance report schema: [schema/conformance_report.schema.json](../schema/conformance_report.schema.json)
- Cases and rejections: https://github.com/contextwindowarchitecture/contextwindowarchitecture/tree/main/conformance
- Assembler page, reports and matrix: https://contextwindowarchitecture.io/assembler.html
- Integration sketch: https://contextwindowarchitecture.io/site/assembly-sketch.txt
- The whole contract in one file: https://contextwindowarchitecture.io/llms-full.txt
