# CWA workshop monorepo: catalog and plan

Status: revision 3, 2026-10-11. Written against the specification draft of 2026-10-07 (R-1 to R-26, spec commit `c252494`, assembler tag `draft-release`). Revision 2 recorded the owner's decisions from the first review; revision 3 records the second round and the first restructuring commit (section 8, step 1, done).

This document proposes turning `contextwindowarchitecture/workshop` into a monorepo of workshops about Context Window Architecture (CWA) and context engineering. It lists each workshop with its objectives, goals, outcomes and calls to action, groups them into learning tracks, sets the repository layout and conventions, and gives the build order.

Vocabulary used below:

- **Objective**: what the facilitator sets out to teach.
- **Goal**: what participants build or do during the session.
- **Outcome**: what participants can demonstrably do afterwards.
- **Call to action**: the next step after the session, in their own organization or in the CWA community.
- **Covers**: the specification requirements the workshop exercises.
- **Reuses**: existing material in the `contextwindowarchitecture` GitHub organization the workshop should vendor or point at rather than rebuild.

## 1. Why the current workshop has to change

The existing content (`chatbots/`, `utils/`, `main.py`, `prereqs/`, `plugins/`) teaches a six-layer "Context Window Model" and demonstrates it by concatenating strings into a system prompt inside Streamlit chatbots. The specification no longer describes layers in a prompt. It describes:

- **Four planes and eleven typed slots**, each item carrying one slot and one authority role (R-1).
- **Producers** that emit scored, provenance-bearing items in batches and report what they suppressed (R-9, R-13, R-14, R-18).
- **An application** that authenticates producers, declares conflict groups, writes state, enforces invariants outside the model, and freezes an immutable snapshot after every external read (R-5, R-8, R-11, R-12, R-15, R-23).
- **An assembler**, a pure function from snapshot to payload plus trace, that admits, resolves, fits, renders and never calls a model (R-16 to R-26).
- **Placement profiles** that are versioned, per route, and evaluated before deployment (R-19, R-20).
- **Three conformance claims**: producer, assembler, application. Assembler claims rest on a published conformance report of 65 cases and 25 rejections.

None of that is in the current code. Decision: the legacy content is deleted, not migrated. The migration workshop (W3) starts from the Fernway docs-QA example instead.

## 2. Global decisions

These apply to every workshop and are not repeated below.

- **Language**: Python only. Differences in the TypeScript, Go and Rust assemblers are noted later as call-outs, not as parallel tracks.
- **Fictional product**: Fernway, the team task tracker and 21-article help centre from the `examples` repository. Workshops link to the matching example where one exists; nothing is forced to fit.
- **Dependencies**: sibling checkouts, as the demo and benchmark repos already do. `shared/siblings.py` resolves `examples`, `assembler-python`, `assembler-demo`, `contextwindowarchitecture`, `website` and `integrations` under one root: the parent of this repository by default, or `CWA_SIBLINGS_ROOT`, absolute or relative. Siblings are pinned to their current release in `shared/contract/pins.json`, never to a branch; repositories with no release yet sit at `main` until they get one. The spec contract is vendored and locked once in `shared/contract/`, the way the assemblers vendor it, from the commit the assembler's release pins.
- **Model access**: no key needed by default. Every lab replays committed snapshots, traces and recorded runs. The live path is an OpenAI-compatible endpoint (Ollama, omlx, vLLM, LM Studio, llama.cpp, Groq, OpenRouter) configured by `OPENAI_BASE_URL`, `OPENAI_API_KEY` and a model name. Anthropic notes come later as a supporting document.
- **Delivery shape**: self-paced first. Each workshop is written as a self-contained module with numbered checkpoints a learner can verify alone. Instructor-led delivery adds a facilitator run sheet on top. Conference delivery is a marked subset of checkpoints. Writing self-paced first makes the other two cheap; the reverse is not true.
- **Two repo-wide rules**, lifted from the examples repository and enforced by lint: participant code never assembles, and never patches an assembler's output.
- **Build order**: W0 first, then W1, then the application-builder track in order (section 8).

## 3. The catalog

### W0. Context engineering foundations: the prompt is compiled output

- **Format**: 90 minutes self-paced or as a talk plus guided browser lab. No local toolchain.
- **Audience**: anyone shipping or planning an LLM feature. No prerequisites.
- **Objectives**
  - Name the seven reproducible failure modes of string-built prompts: authority inversion, instruction-shaped evidence, stale-as-current, memory that never expires, displacement under budget, redundant re-reading, missing trigger.
  - Present the evidence on placement and length: Lost in the Middle, RULER, NoLiMa, the Anthropic and OpenAI prompting guides, and provider prompt-cache rules.
  - Introduce the six terms a learner needs before anything else: item, slot, snapshot, assembler, profile, trace.
  - State rule zero: language guidance goes in context, enforceable invariants go outside the model (R-5).
- **Goals**
  - Run the landing-page assembly demo through the budget squeeze and the "remove a slot" controls, and reproduce each failure mode once.
  - Paste your own system prompt into the Start-page migrator, read the "% tokens with no owner" figure, and export `items.cwa.yaml`.
- **Outcomes**
  - Can explain in two minutes why a model request should be assembled from typed slots rather than concatenated.
  - Leaves with a slot inventory of one real prompt they own.
- **Calls to action**
  - Bring the exported `items.cwa.yaml` to W1 and W3.
  - Read the Start page's six steps and note which ones the team already does.
- **Covers**: R-1, R-5, R-7 at the level of ideas; no code.
- **Reuses**: `website/index.html` demo and tour, `website/start.html` migrator, `website/evidence.html`, `site/glossary.json`.

### W1. The CWA tour: planes, slots, snapshot, trace

- **Format**: half day, hands-on, model-free.
- **Audience**: engineers. Prerequisite: W0 or equivalent reading. Toolchain: Python 3.12, uv, Node 22 for the inspector.
- **Objectives**
  - Walk the full lifecycle on one request: producers emit, the application freezes, the assembler decides, the trace explains, the provider receives the payload unchanged.
  - Teach trace literacy: `included`, `excluded` with reason codes, `compressed`, `conflicts`, `defaults_filled`, `refused`, `recovery.action`, `snapshot_digest`, `result.hash`.
  - Distinguish the three results: assembled, refused (valid snapshot, trace, no payload), rejected (invalid snapshot, no trace).
  - Show that every reason code is owned by a numbered requirement.
- **Goals**
  - Diff `before.py` against `after.py` in the docs-QA example and find the one function that changed.
  - Run the five basic and six intermediate inspector scenarios. Before each run, predict the reason codes the trace will contain, then check.
  - Break things on purpose: drop the query (`required_slot_missing`), shrink the budget (`protected_content_over_budget`), paste an imperative into a retrieved chunk and confirm nothing changes.
  - Replay a snapshot and confirm byte-identical payload and hash (R-23).
  - Work through the §6.1 test table as a checklist: snapshot, golden task, counterfactual ablation, conflict, budget pressure, freshness, refusal, capability source, cache reuse.
- **Outcomes**
  - Can read any trace and name the requirement behind every exclusion and refusal.
  - Can tell a producer bug from an assembler bug from an application bug by looking at the four inspector columns.
- **Calls to action**
  - Pick the track (section 4) that matches your role.
  - Review one of the demo's unreviewed `scenario.json` expectations and submit the review upstream.
- **Covers**: R-1, R-2, R-4, R-7, R-16, R-17, R-21, R-22, R-23.
- **Reuses**: `examples/01-docs-qa`, `assembler-demo` inspector and tours, `contextwindowarchitecture/examples/*.json`, `contract/reasons.json`.

### W2. Building a conformant producer

- **Format**: half day.
- **Audience**: backend engineers who own retrieval, memory, state or tool integrations. Prerequisite: W1.
- **Objectives**
  - Define the producer conformance claim and what admission can and cannot verify.
  - Teach the seven producer kinds and the slot gate for each: retrieval, memory, state, mcp, capability_policy, policy, interaction.
  - Teach the item: eight required fields, six policy fields and their defaults, scope keys where a missing key is never a wildcard, freshness versus expires, trust as a self-claim.
  - Teach the batch: one per producer, `excluded` rows with `duplicate_of` or `superseded_by` naming a candidate in the same batch, ids unique across the snapshot.
  - Teach precomputation: scores and variants are computed and cached by content hash before assembly, and assembly never calls a model (R-18).
- **Goals**
  - Lab A, retrieval: write a producer from scratch over the Fernway help centre that emits one scored item per chunk, drops its own near-duplicates and reports each as `duplicate_content`, and attaches a precomputed summary variant.
  - Lab B, memory: emit only live entries with `expires` and a `turn:` source, and report expired and revoked entries by id without their bodies (R-14).
  - Lab C, state: emit one typed item per fact with freshness equal to the read time, and watch `stale_state` appear when `max_age_seconds` passes (R-8).
  - Lab D, negative tests: claim a higher tier (`tier_upgrade_not_allowed`), send to a wrong slot (`producer_slot_not_allowed`), omit the injection marker (`untrusted_content_unmarked`), reuse an id (`duplicate_item_id`).
  - Lint every item and batch with the browser checkers, then freeze a snapshot and read `defaults_filled` and `excluded` in a real trace.
- **Outcomes**
  - Ships a producer package with a test suite that asserts the batch shape and the reason codes it must never trigger.
  - Holds a one-page producer conformance checklist for code review.
- **Calls to action**
  - Continue to W9 module A to wrap a tool you already run instead of writing from scratch.
  - Follow the "build a producer" contribution path on the About page.
- **Covers**: R-1, R-2, R-3, R-9, R-10, R-13, R-14, R-15, R-18, R-24 to R-26 as route opt-ins the producer must anticipate.
- **Reuses**: `guides/producers.md`, `website/producers.html` linters, `assembler-demo/producers/`, `examples/02-account-aware/producers.py`.

### W3. Integrating CWA into an existing application

- **Format**: full day. Can be split into W3a (the migration) and W3b (framework seams).
- **Audience**: application engineers. Prerequisite: W1; W2 recommended.
- **Objectives**
  - Define the application conformance claim: the MUSTs no component can meet on the application's behalf.
  - Teach the migration sequence from the Start page: name the slots you already send, freeze a snapshot, give every item an authority and a source, check the trace, pick a profile, move enforcement out of the prompt.
  - Teach the application's duties: authenticate producers and bind identity outside item fields (R-15), write state from the application never from model output (R-8), declare typed conflict groups (R-11), set `budget.input` from the model's context limit less `reserved_output` (R-16), set `parser: true` where a downstream parser exists (R-4), freeze before every model call and refreeze for any retry (R-12, R-23), hand the payload over unchanged with no text of its own.
  - W3b: show the seam in each framework where assembly belongs, including OpenAI Agents SDK `call_model_input_filter`, LangGraph, Claude Agent SDK, Vercel AI SDK and roll-your-own, and when to skip CWA.
- **Goals**
  - Start from a Fernway "before" application: the docs-QA `before.py` extended with the account lookup and memory store from the account-aware example, all still concatenated into one prompt. Inventory it into slots. Replace the string builder with producers plus freeze plus assemble. Hand the payload to an OpenAI-compatible endpoint through a thin adapter.
  - Add a route policy, a budget, a tokenizer with margin, a draft profile, scope keys for tenant and user, one fact conflict group with producer precedence, and scenario checks that fail CI when context drifts.
  - Add one guard outside the model for a rule the old prompt only stated.
  - W3b: wire the same assembly into one framework of choice and prove the payload reaches the model byte for byte.
- **Outcomes**
  - A migrated application whose every model call has a snapshot, a trace and a replayable digest.
  - A written list of which conformance duties the application now meets and which remain open.
- **Calls to action**
  - Run the same inventory on one production prompt and file the slot map in the team's design docs.
  - Report an inexpressible route to the spec repository if the migration hits one.
- **Covers**: R-4, R-5, R-7, R-8, R-11, R-12, R-15, R-16, R-19, R-20, R-23.
- **Reuses**: `examples/01-docs-qa` and `02-account-aware` as the before and after poles, `website/start.html` scaffolds, the landing page's framework seam picker.

### W4. Budgets, variants, routes and refusals

- **Format**: half day.
- **Audience**: engineers who own cost, latency or model selection. Prerequisite: W1.
- **Objectives**
  - Teach the fitting model: protected, compressible and droppable tiers; item `token_budget`; slot `max_tokens` and `min_tokens`; `budget.margin_percent`; shed order and `fitting_order`; variants before omission.
  - Teach refusals as outcomes, not errors: `protected_content_over_budget`, `slot_floor_over_budget`, `evidence_required`, each with a recovery action.
  - Teach tokenizers: the published estimate with a margin versus an application tokenizer under its own id, and why a published id can never be overridden (R-16).
  - Teach multi-route escalation: a small route refuses, the application builds a new snapshot on a larger route.
- **Goals**
  - Precompute summaries for the help centre keyed by content hash, review them for faithfulness, and commit only the faithful ones (the examples repo found 5 of 80 local-model summaries were wrong).
  - Configure two routes with different budgets and models on the OpenAI-compatible endpoint and an escalation table. Trigger the refusal with a pasted log and watch the escalation.
  - Calibrate a margin: compare the estimate tokenizer against the serving model's real tokenizer on the route's own text, then set `margin_percent` from the measured error.
  - Walk the `budget-*` conformance cases and predict each outcome before running it.
- **Outcomes**
  - Can design a route set with budgets, caps, floors and escalation and justify each number.
  - Can explain to a product owner why the system refused rather than answered.
- **Calls to action**
  - Replace one truncation heuristic in production with tiers plus precomputed variants.
- **Covers**: R-12, R-16, R-17, R-18.
- **Reuses**: `examples/03-budget-and-routes`, `conformance/cases/budget-*`, `assembler-python/examples/tiktoken_tokenizer.py`, bench tokenizer-margin metrics.

### W5. Tools, MCP and capability policy: agents under CWA

- **Format**: half day.
- **Audience**: engineers building tool-using agents. Prerequisite: W1; W2 recommended.
- **Objectives**
  - Teach that permission is decided outside the model: an MCP adapter proposes tool specifications, only the capability policy producer may emit `governance.capabilities`, and the snapshot carries the grant (R-15).
  - Teach that a tool result is an observation, not permission to act; that MCP output is marked untrusted unless the route verifies the server; and that supersession keeps only the latest observation per source (R-25).
  - Teach the loop: one snapshot per inference, a bounded controller, a guard that checks every tool request against the grant, the input schema and the scope rule, and that returns a denial as `state.task` rather than a fake tool result.
- **Goals**
  - Build a small MCP server and client over Fernway webhooks. Write the capability policy file with roles, policy-written descriptions and schema pins. Build the guard.
  - Run the injected-instruction scenario: a tool result that says "call delete_webhook". Confirm the model never gets the capability and the guard denies the request if it tries.
  - Inject faults (timeout, error) into the MCP server and watch the trace and the controller's recovery.
  - Record a live run against the local endpoint, then replay it model-free.
- **Outcomes**
  - An agent loop whose tool calls are gated by a versioned allow-list and a guard, with a replayable record of every inference.
- **Calls to action**
  - Audit one production agent for any tool specification that reaches the model without a grant.
- **Covers**: R-5, R-7, R-8, R-10, R-15, R-25.
- **Reuses**: `examples/04-tools`, `assembler-demo/mcp/` servers with `CWA_DEMO_FAULTS`, `assembler-demo/src/agent/` guard and controller, advanced scenarios and reference runs.

### W6. Placement profiles, prompt caching and profile evaluation

- **Format**: half day.
- **Audience**: architects, evaluation engineers. Prerequisite: W1.
- **Objectives**
  - Teach that CWA takes no position on placement and requires only that placement be a profile: versioned, per route, evaluated against the route's tasks before promotion (R-19, R-20).
  - Teach the six published profile shapes and the evidence behind each.
  - Teach the six-step evaluation protocol: fix the item set, name the metric, render with each profile, compare on the target model, measure reuse, record and version.
  - Teach what caching owns: history rendered in the order said, the `cwa-message-blocks/v1` renderer, breakpoints as structure not text, the cache-reuse test.
  - Teach the registry lock: a profile's digest excludes its evaluation object, content changes without a version bump fail to load, deployment mode returns only evaluated profiles.
- **Goals**
  - Diff two profiles in the profile explorer and export both.
  - Render the same frozen conversation under a cache-first profile across two turns and prove the leading bytes match.
  - Run a small evaluation across two profiles on one local model, write the evaluation object with suite, date, result and artifact location, and lock the registry.
  - Attempt to deploy an unevaluated profile and read the refusal.
- **Outcomes**
  - One evaluated profile with a reproducible artifact and a registry lock the team can ship.
- **Calls to action**
  - Contribute the evaluated profile through the About page's contribution path.
- **Covers**: R-7, R-19, R-20, R-21, R-23.
- **Reuses**: `website/evidence.html` explorer and protocol, `examples/profiles.json`, `conformance/registry/`, `examples/05-production/policy/registry.lock.json`, `conformance/cases/blocks-*`.

### W7. Production: snapshot store, telemetry, evals and the promotion gate

- **Format**: half day.
- **Audience**: platform and SRE engineers. Prerequisite: W1; W6 recommended.
- **Objectives**
  - Teach the snapshot store as the unit of debugging: runs, show, replay, what-if against a candidate policy.
  - Teach telemetry that carries digests and reason codes but never user text, exported over OTLP.
  - Teach evals graded against the run record: cites what it was sent, claims match actions, must-call and must-not-call, and a promote step that refuses without passing results.
  - Teach the mapping from refusals to host outcomes: needs-info, requires-manual-review, precompute and retry.
- **Goals**
  - Run `whatif` against a stricter-relevance candidate and read how many inferences would change.
  - Export spans to a local collector and find one assembly by its digest.
  - Grade a committed eval result, then try to promote a profile that scored five of six.
- **Outcomes**
  - An operating playbook: what to store, what to emit, what gates a deployment, how to triage a refusal.
- **Calls to action**
  - Add the snapshot digest and refusal reason to your existing observability dashboards.
- **Covers**: R-12, R-17, R-19, R-20, R-21, R-22, R-23.
- **Reuses**: `examples/05-production`, `integrations/fullsend/README.md` §4.5 and §4.6.

### W8. Inside the assembler: the repair kata

- **Format**: full day.
- **Audience**: engineers who want to contribute to the reference assemblers. Prerequisite: W1. Toolchain: Python 3.11 or later, uv.
- **Decision**: kata form only. Four assemblers already exist, so the goal is contributors to them, not new ports. The porting workflow is covered as reading, not as a lab.
- **Objectives**
  - Teach the assembler as a pure function with four exits: assembled, refused, rejected, stopped on a published-id override.
  - Teach the pipeline in order: validate and snapshot checks, admit, resolve conflicts, supersede, dedupe, diversity cap, refusal checks and fitting, render, trace.
  - Teach the normative order of reason codes and why the earliest applicable code wins (R-21).
  - Teach the portability traps that bite in any language: UTF-16 code-unit ordering, the ECMAScript whitespace set, doubles beyond 2^53, lone surrogates, full-precision instants, RFC 8785 canonical JSON, own-key lookups, ECMAScript regex semantics.
  - Teach contributor readiness: the working rules in the ports' `AGENTS.md` (never read another port's code, route spec gaps to the spec repo first), the `PENDING` set that only shrinks, `status.json` and the assembler-scope file, the conformance report and how a listing is imported, the commit conventions.
- **Goals**
  - Receive a fork of `assembler-python` with roughly ten injected defects, each breaking one or two conformance cases and each in a different pipeline stage. A sealed manifest maps defect to case and requirement.
  - For each failing case: read `case.json` and its `rules`, read the normative text, locate the stage, fix it, and re-run until the report shows 65 passed and 25 rejected with a clean contract.
  - Write one new unit test per defect in the style of the existing test suite.
  - Produce the conformance report and run the report checker as a real contributor would.
- **Outcomes**
  - Can read a conformance report and know exactly which stage is wrong.
  - Has made changes to the reference assembler under its own test discipline and is ready to open a real pull request.
- **Calls to action**
  - Pick an open issue in one of the four assembler repositories.
  - File a case-problem issue for any case whose expectation you can show is wrong.
- **Covers**: every assembler-scope requirement through the cases; R-2, R-16, R-17, R-21, R-22, R-23 directly.
- **Reuses**: `assembler-python` and its tests, `assembler-template/PORTING.md` as reading, `conformance/README.md`, `contract/assembler-scope.json`.

### W9. Adapters

The word "adapter" names four different things around an assembler. Each is one module; a facilitator can run one or all four. Module A is the one most teams need first.

- **Format**: half day per module.
- **Audience**: integrators and platform engineers. Prerequisite: W1; W2 for module A; W8 helps for module B.

**Module A. Tool-to-producer adapters: making what you already run emit CWA batches**
- Objectives: most teams already have a retriever, a vector store, a memory layer, a CRM client, a feature store or an MCP server. None of them emits items. An adapter sits between the existing tool and the snapshot and turns the tool's native output into a conformant producer batch, without changing the tool. Teach the adapter's duties: map native results to items with the right slot and authority, assign `source` and `source_version` from the tool's own identifiers, compute or pass through relevance, drop and report near-duplicates, mark `injection_risk`, attach precomputed variants, report suppressed entries, and let the application bind the producer identity outside the items.
- Goals: build three adapters against real libraries. A LlamaIndex or LangChain retriever to a retrieval producer. A key-value or SQL memory table to a memory producer that reports expired and revoked rows. An MCP server's tool results to an mcp producer, with a tool-specification proposal going to the capability policy rather than to `governance.capabilities`. Run each through admission and read what it still gets wrong.
- Outcomes: a reusable adapter pattern and a checklist for wrapping any further tool.

**Module B. The assembler adapter protocol and the harness**
- Objectives: the stdin snapshot and exit-code protocol (0 assembled or refused, 2 rejected, 3 unsupported) that lets any assembler be driven as a black box; the four-way agreement check; expectations generated by one assembler and reviewed by a person.
- Goals: write a Python adapter for an assembler, plug it into the demo harness, run compare and read the first difference as a JSON pointer.
- Outcomes: can add any assembler to the demo, the conformance runner and the viability benchmark.

**Module C. The provider adapter**
- Objectives: the `cwa-messages/v1` render shape as the intermediate representation; mapping system, tools and messages to an OpenAI-compatible request with no text of the adapter's own; `max_tokens` from `reserved_output`; cache breakpoints as structure that adds no text so the traced count and hash still describe what the model reads.
- Goals: write a provider adapter for the OpenAI-compatible endpoint, generate the copy-pasteable SDK snippet for a payload, and prove by hash that the request body equals the payload. Anthropic as a reading exercise.
- Outcomes: can add a new provider without touching assembly.

**Module D. Host and framework seams**
- Objectives: where assembly sits in an agent framework, and how an existing host's permission model becomes authority. The fullsend integration is the worked example: repository permission decides who is `user` in history and whose words are evidence, the hidden HTML-comment injection is escaped, a comment flood is deduped and capped per author, and a policy bug that drops a high-severity finding is visible in the trace before the fix.
- Goals: build a briefing producer set for a host of your choice, map one refusal to a host outcome, and write the before and after pages.
- Outcomes: a pattern for integrating CWA into a system that already has its own notion of who is allowed to speak.

- **Calls to action**: contribute an adapter back to `examples`, `assembler-demo` or `integrations`.
- **Covers**: A: R-1, R-2, R-9, R-10, R-13, R-14, R-15, R-18. B: R-17, R-21, R-23. C: R-7, R-16, §1 handoff. D: R-6, R-7, R-10, R-11, R-24, R-26.
- **Reuses**: `assembler-demo/producers/retrieval.py` (a LlamaIndex adapter in all but name), `examples/04-tools/tools.py`, `assembler-demo/adapters/`, `src/harness/compare.mjs`, `src/provider/`, `integrations/fullsend/`.

### W10. Conformance and contributing to the specification

- **Format**: half day.
- **Audience**: anyone who has finished W2 or W8 and wants to change the spec.
- **Objectives**
  - Teach the case anatomy: `case.json`, `snapshot.json`, `expected.trace.json`, `expected.payload.txt`, and the rejection anatomy with no trace.
  - Teach that generators derive expectations from a table of intended outcomes, never from an assembler's logic.
  - Teach the contract as data: requirements, reasons in precedence order, slot defaults, model, and `check.py --write` regenerating the spec text.
  - Teach the revision process (proposal, draft, revision, version) and the three issue templates: case problem, spec change, implementation listing.
- **Goals**
  - Write a new generator entry for a behaviour you believe is under-tested, regenerate, review the diff, run every assembler against it.
  - Draft a spec-change issue with the requirement text, the reason code if any, the schema change and the cases that would prove it.
- **Outcomes**
  - A pull-request-ready conformance case and a well-formed spec-change proposal.
- **Calls to action**
  - Open the issue or pull request.
- **Covers**: R-21, R-22, §1 conformance claims.
- **Reuses**: `conformance/generators/`, `conformance/check.py`, `conformance/import_report.py`, `.github/ISSUE_TEMPLATE/`.

### W11. Benchmarking CWA: does it help, and what does the number mean

- **Format**: half day.
- **Audience**: evaluation engineers, technical leaders deciding adoption.
- **Objectives**
  - Teach the two benchmark families: the examples bench (one application, fourteen models, constructs mapped to requirements, invariants that must never fail) and the viability benchmark (Domain 1 black-box assembler determinism and fuzzing, Domain 2 long-horizon conversation arms).
  - Teach the interpretation layer: which numbers are evidence about CWA, which are the model's doing, which are the host's.
  - Teach the headline finding and its limits: application-written state scores 0.97 to 0.99 against 0.82 for pinned truncation, model-written state is about level, history format alone gains nothing.
  - Teach cost planning before any run, and tokenizer margin measurement across models.
- **Goals**
  - Replay a committed Domain 2 run with no GPU and read the arms.
  - Regrade a committed examples-bench run from files with no model and read the construct table.
  - Design one new arm or construct and write its expectation.
- **Outcomes**
  - Can run, read and critique a CWA benchmark and tell which claims it supports.
- **Calls to action**
  - Add one construct from your own domain to the expectations file and run it on one model.
- **Covers**: R-13, R-16, R-19, R-23 as measured properties.
- **Reuses**: `examples/bench`, `cwa-extended/benchmark` and `benchmark-ui`.

### Capstones: build a conformant application in a domain

Team exercises of one day each. Each starts from the skeleton of W5 and W7 (producers, context, a policy folder with route policy, profile, capabilities and routes, scenario checks, an eval suite) and ends with a W7-style gate: write cases, record, grade, promote.

The three blueprints in `cwa-extended` (scribe and diagnostic assistant, customer support and logistics router, wealth management and triage) seed the domains, but they predate the current snapshot shape and must be rewritten before use. Known gaps: `batch` instead of `batches` with a producer object, no route policy object, an integer `assembly_time`, tiers and dedupe placed in the profile instead of the route policy, a claimed `evaluated` status with no artifact, and a conflict tie-breaker that reads content rather than producer precedence. They also assume a fast classifier model called "Jev" for pre-assembly scoring and gating. That name comes from a pasted conversation in `cwa-extended/notes.md` and does not appear anywhere in the specification, the examples or the assemblers. The capstones replace it with a generic, deterministic pre-assembly scorer so every scenario stays replayable; if a real scorer is adopted later it becomes one more producer.

- **C1. Scribe and diagnostic assistant**: transcript as untrusted history, EHR as protected task state, reranked guidelines as evidence with `requires_evidence`, a gated prescription capability, a SOAP-note output contract. Scenarios: transcript injection, EHR-versus-telemetry fact conflict, prescription guard, refusal when no guideline survives.
- **C2. Customer support and logistics router**: intent classification selects the route policy, CRM history with precomputed variants, ticket state as task state, dedupe and per-source caps, small and large routes with escalation, a PII screen as a guard outside the model.
- **C3. Wealth management and triage**: ledger precedence over market data in fact groups, protected user state, a strict output contract, a capability guard on trades, cache-stable placement measured across turns.

## 4. Tracks

Everyone starts with W0 and W1. After that:

| Track | Who | Sequence |
| --- | --- | --- |
| Application builder | engineers shipping an LLM feature | W2, W9 module A, W3, W4, W5, W6, W7, then a capstone |
| Contributor to the assemblers | engineers who want to work on the reference implementations | W8, W9 module B, W10, W11 |
| Integrator | framework and host owners | W9 modules A, C and D, W3b, W5 |
| Evaluator and architect | leads deciding adoption, eval engineers | W6, W7, W11, then critique a capstone |
| Spec contributor | anyone joining the project | W2 or W8, then W10 |

Conference cuts: W0 alone as a talk, W0 plus W1 as a half-day tutorial, W1 plus W3a as a one-day "migrate your app" workshop.

## 5. Repository layout and conventions

```
workshop/
  README.md                    catalog, tracks, prerequisite matrix, how to run any lab
  docs/
    plan/workshops.md          this document
    facilitator/               per-workshop run sheets, timing, common stumbles, conference cuts
    glossary.md                vendored from the website's glossary
    setup.md                   toolchain install, sibling checkout layout, offline bundle
    providers/                 openai-compatible.md now; anthropic.md later
  shared/
    contract/                  vendored spec contract and lock, one pin for the whole repo
    siblings.py                resolves ../examples, ../assembler-python and so on; env override
    fixtures/                  recorded runs and snapshots shared across labs
    tools/                     check_scenarios.py, replay.py, env templates, model-free CI runner
  00-foundations/
  01-cwa-tour/
  02-producers/
  03-integration/
    before/                    the concatenated Fernway app participants migrate
    solution/
  04-budgets-routes/
  05-tools-mcp/
  06-profiles-caching-eval/
  07-production/
  08-assembler-kata/
    defects.sealed.json        defect manifest, revealed per checkpoint
  09-adapters/
    a-tool-to-producer/
    b-assembler-protocol/
    c-provider/
    d-host-seam/
  10-conformance-contribution/
  11-benchmarking/
  capstones/
    scribe-diagnostic/
    support-logistics-router/
    wealth-triage/
```

Conventions:

- Each numbered directory is self-contained: its own `README.md` with objectives, goals, outcomes, checkpoints and calls to action copied from this catalog, its own `pyproject.toml` managed by uv, a `scenarios/` folder of committed snapshots, traces and payloads, and a `scenarios.py --check` that CI runs without a model.
- Participant code never assembles and never patches an assembler's output. Enforced by a repo-wide lint in `shared/tools/`.
- Sibling checkouts resolve through `shared/siblings.py`: default the parent of this repository, overridable by `CWA_SIBLINGS_ROOT`. `shared/contract/pins.json` names the release each sibling should be at, and `shared/tools/clone_siblings.py` clones the missing ones there. CI does the same.
- One spec pin for the whole repository in `shared/contract/`, re-vendored deliberately with a changelog entry, because a re-vendor can change cases.
- Solutions live beside each lab in `solution/`, not on a branch, so a facilitator can diff live.
- No key required by default. Every live path reads a `.env` from `.env.example` with `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `CWA_WORKSHOP_MODEL`, and prints the request instead of sending it when no provider is set. Reasoning models get a low reasoning-effort default so they do not spend `reserved_output` thinking.
- Checkpoints are the unit of progress. Each is a command a learner runs and an expected result they compare, so self-paced, instructor-led and conference delivery share one source.
- The legacy tree (`chatbots/`, `utils/`, `main.py`, `prereqs/`, `plugins/`, `.streamlit/`, `OAUTH_SETUP.md`, `.config.yml`, `requirements.txt`, the three root PNG logos) is deleted in the first restructuring commit. `SHOULDERS.md` and `LICENSE` stay.

## 6. Decisions recorded on 2026-10-11

1. "Adapter" means, first of all, wrapping an existing tool so it works with an assembler. That is W9 module A, and the other three meanings stay as modules B to D.
2. The legacy Streamlit chatbots are deleted. W3 starts from the Fernway docs-QA example.
3. Fernway is reused. The workshop and examples repositories are linked where it helps and nowhere else.
4. Python only. Other-language differences become call-outs later; examples in all four assemblers may follow later.
5. W8 is a kata on a fork of the reference assembler. Its purpose is contributors to the four existing assemblers, not new ports.
6. The default live provider is any OpenAI-compatible endpoint. Anthropic gets a supporting document later.
7. Self-paced first, because it makes instructor-led and conference delivery subsets rather than rewrites.
8. "Jev" is an artifact of a pasted conversation and old blueprint files, not part of CWA. The blueprints are rewritten and the scorer is generic and mocked.
9. Sibling checkouts plus simple vendoring of the contract, as the other repositories do.
10. Build starts at W0.

## 7. Decisions recorded in the second round, and what stays open

Decided:

11. Sibling location is an environment variable, `CWA_SIBLINGS_ROOT`, accepting absolute or relative paths, because the same mechanism serves CI, containers and any other place a path is needed.
12. The restructure started: the legacy tree is deleted, the layout exists, W0 is written, and the shared tooling runs.
13. The kata fork tracks `draft-release` for now. The general rule is the current release, never a branch, for every pin in this repository.
14. The blueprint rewrites happen here, under `capstones/`.
15. The kata's defect manifest lives in this repository, at `08-assembler-kata/defects/`, with `kata.py` as the injector; the participant tree (`work/`) is rebuilt from the sibling at its pin and is never committed. Recorded 2026-10-11, after the kata had been regenerated this way through the build. A private branch of the reference assembler would tie the kata to that repository's history for no gain.
16. The other-language call-outs the language decision deferred are one page, [docs/assemblers.md](../assemblers.md): the four ports side by side and what changes per module. It is updated in the same commit as any pin move.

Open:

1. **Examples repo linkage.** The lightest link is a "Workshops" section in the examples README and the pointer each workshop README already carries. Anything heavier is left for later. This is a change to the `examples` repository.

## 8. Build order

1. Done. Restructure: legacy deleted, layout created, `shared/` tooling and vendored contract, `docs/setup.md`, CI, W0 written with worksheet and run sheet.
2. Done. W0, then W1. Together these are the half-day tutorial and the one-week-out talk material.
3. Done. W2 and W9 module A.
4. Done. W3a, W4, W5; the "migrate your app" one-day offering (W1 plus W3a) exists.
5. Done. W6, W7 and the first capstone, C2.
6. Done. W8, W9 modules B and C, W10 and W11.
7. Done. W3b, W9 module D, the capstones C1 and C3, and the Anthropic provider notes.
8. The catalog is built. What follows is upkeep: move the pins together and re-vendor the contract when the specification or the assembler releases, rerun every `scenarios.py --check` and the W11 invariants, run the capstone suites live when a model is at hand and promote the profiles from the live reports, and send the W10 case and any new one upstream.
