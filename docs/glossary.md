# Glossary

Generated from the website's `site/glossary.json` by `shared/tools/glossary.py`. Do not edit by hand; re-run the script after the website changes. Each entry gives the plain meaning, then the specification's own words, then where the site shows it.

## admission

The assembler's first step. Each candidate item is checked against its schema and the route: who sent it, which slot, what authority, its scope, age, expiry and relevance. Each is admitted, or excluded with a reason code the trace records.

> The last four are the assembler's, and everything it leaves out shows up in the trace with a reason code.

Where: [Spec §4](https://contextwindowarchitecture.io/spec.html#s4)

Related: `exclusion`, `route-policy`, `item`, `trace`

## application

The system that calls the assembler: it runs the producers, authenticates each one, freezes the snapshot, hands the payload to the model, and enforces invariants and tool permissions outside the model.

> A conformant application uses a conformant assembler and only conformant producers, and meets the MUSTs no component can meet for it

Where: [Spec §1](https://contextwindowarchitecture.io/spec.html#s1)

Related: `producer`, `assembler`, `snapshot`, `rule-zero`

## assembler

The component that turns a frozen snapshot into a rendered payload and a trace: it admits or excludes each item, resolves the declared conflicts, fits what is left to the budget in tier order, and renders in the profile's order. It never calls a model and reads nothing but the snapshot.

> A conformant assembler meets every MUST an assembler can meet by itself, provides every tokenizer and renderer that Tokenizers and renderers in conformance/README.md requires, and can emit its trace as JSON with the fields R-21 lists.

Where: [the Assembler page](https://contextwindowarchitecture.io/assembler.html)

Related: `snapshot`, `payload`, `trace`, `admission`, `conformance`

## authority

Who an item speaks for, one of seven values: governing, user, state, reference_only, observation, generated and untrusted. Only governing and user items can direct the model; the other five say where data came from and never rank which fact is true.

> These values classify instruction authority or data provenance; they MUST NOT form a global factual ranking.

Where: [Spec §3.1](https://contextwindowarchitecture.io/spec.html#s3)

Related: `trust`, `injection-risk`, `conflict-group`, `governance`

## batch

What a producer hands over for one call: its candidate items and one row per entry it suppressed, with a reason. The application binds the batch to the producer identity it authenticated; a snapshot holds at most one batch per producer.

Where: [Spec §4](https://contextwindowarchitecture.io/spec.html#s4)

Related: `producer`, `snapshot`, `exclusion`

## budget

The token ceiling for one request. budget.input is the model's context limit less the output reserved for the answer, and margin_percent covers an estimating tokenizer's error. Fitting sheds items in tier order until the payload fits, or refuses.

> sets budget.input to the model's context limit less budget.reserved_output (R-16)

Where: [Spec R-16](https://contextwindowarchitecture.io/spec.html#R-16)

Related: `tier`, `tokenizer`, `refusal`

## capability policy

The application's versioned allow-list of tools per route and user, and the only producer for governance.capabilities. Adapters propose tool specifications; the policy admits the ones this user may use; the application's tool guard still enforces each call.

Where: [Spec §3](https://contextwindowarchitecture.io/spec.html#s3)

Related: `producer`, `governance`, `rule-zero`, `mcp`

## chunk

The piece of a document a retriever pulls. Each is sent as its own evidence item with its source, source version and relevance score, never merged into one blob.

> the piece of a document a retriever pulls is a chunk.

Where: [Spec §2](https://contextwindowarchitecture.io/spec.html#s2)

Related: `evidence-plane`, `producer`, `deduplication`

## conflict group

A set of items the application declares as disagreeing, typed as an instruction conflict or a factual one. Instruction conflicts are settled by authority and the peers' conflict policies, factual ones by the route policy for that fact. The assembler never finds contradictions by reading prose.

> An assembler MUST classify supplied conflict groups as instruction or fact before resolution.

Where: [Spec R-11](https://contextwindowarchitecture.io/spec.html#R-11)

Related: `authority`, `route-policy`

## conformance

The three claims the specification defines, for a producer, an assembler and an application. An assembler's claim rests on a report that passes every published case and rejects every published rejection; a producer's or an application's rests on its word.

> These are the only claims this specification defines. An application is not conformant because one of its parts is, though it may say which of its parts are.

Where: [Spec §1](https://contextwindowarchitecture.io/spec.html#s1)

Related: `conformance-case`, `assembler`, `producer`, `requirement`

## conformance case

A published test for assemblers: a snapshot in, the expected trace and payload out. A rejection case is a snapshot that breaks exactly one check and must be rejected before assembly. Each implementation's report counts the cases it passes.

Where: [the Assembler page](https://contextwindowarchitecture.io/assembler.html)

Related: `conformance`, `rejection`, `snapshot`

## deduplication

A route option on a slot. Items whose bodies are equal once whitespace is collapsed are reduced to the highest-ranked copy, and the rest are excluded as duplicate_content. A retriever reports its own near-duplicate drops the same way.

Where: [Spec R-24](https://contextwindowarchitecture.io/spec.html#R-24)

Related: `supersession`, `source-diversity`, `chunk`

## eligibility

A short note on why an item belongs in the request, for whoever reads the trace. It is text, never code: the route's slot rules are the predicate that decides.

> eligibility is descriptive text, not executable code; the route's versioned slot rules are the executable eligibility predicate.

Where: [Spec R-3](https://contextwindowarchitecture.io/spec.html#R-3)

Related: `route-policy`, `trace`

## evaluated profile

A profile is promoted for deployment only by evidence from its own route: a model version, a suite, a date, results and a reproducible artifact. Every profile on this site is unevaluated, a hypothesis to test before use.

Where: [evaluating a profile](https://contextwindowarchitecture.io/evidence.html#evaluate)

Related: `profile`, `placement`

## evidence

The plane that holds what the model may ground on: retrieved chunks and tool observations, each its own item with provenance, freshness and trust, treated as reference material and never as instruction. Not the Placement page, which collects the evidence for making placement a profile.

> An item in one of the two evidence slots is an evidence item, and the piece of a document a retriever pulls is a chunk.

Where: [the schema](https://contextwindowarchitecture.io/index.html#planes)

Related: `plane`, `chunk`, `placement`, `injection-risk`

## exclusion

An item left out of the payload, recorded in the trace with a reason code such as missing_field:relevance, out_of_scope or over_budget, and the stage that decided it, producer or assembler.

Where: [Spec §4](https://contextwindowarchitecture.io/spec.html#s4)

Related: `admission`, `trace`, `refusal`

## expires

An item's deadline. An item whose expires is at or before the assembly time is expired and excluded, and every memory entry must carry one.

> expires is a separate deadline: an item whose expires is at or before assembly_time is expired (R-9).

Where: [Spec R-9](https://contextwindowarchitecture.io/spec.html#R-9)

Related: `freshness`, `memory`

## freshness

When an item's content was observed or true, as a date-time. It is not an expiry: expires is a separate deadline.

> freshness is an RFC 3339 date-time recording when the fact was observed or true; it is not an expiration time.

Where: [Spec R-2](https://contextwindowarchitecture.io/spec.html#R-2)

Related: `expires`, `item`, `supersession`

## governance

The plane that says who may direct the model: instructions, admitted capabilities, steering examples and the output contract. It is versioned like code and never overridden by anything below it. Not the project's revision process, which the About page describes.

Where: [the schema](https://contextwindowarchitecture.io/index.html#planes)

Related: `plane`, `authority`, `rule-zero`, `capability-policy`

## harness

The agent framework or loop that runs the tools, keeps the state and retries the failures. CWA fills the one blank it leaves: what lands in the window on each pass.

Where: [harness engineering](https://contextwindowarchitecture.io/assembler.html#harness)

Related: `application`, `assembler`

## injection risk

A marker, untrusted_content, on every item whose body might carry an injection: retrieved chunks, tool output, memory, history and the query. It never changes authority or placement; it keeps unmarked and unverified material out of governance.

> injection_risk: untrusted_content when the body might carry an injection, whatever its authority.

Where: [Spec R-10](https://contextwindowarchitecture.io/spec.html#R-10)

Related: `trust`, `authority`, `admission`

## interaction

The plane that holds what has happened and what is asked: compressed memory, the recent turns as a transcript, and the live query that triggers generation. The query is never omitted and always carries user authority.

> The query is never omitted and always carries user authority.

Where: [the schema](https://contextwindowarchitecture.io/index.html#planes)

Related: `plane`, `memory`, `authority`

## item

One governed piece of context in a slot: a policy, a retrieved chunk, a tool observation, a memory entry, a turn. Each carries its source, source version, authority and freshness, and the assembler admits or excludes each one on its own.

> A model call is assembled from items.

Where: [Spec §2](https://contextwindowarchitecture.io/spec.html#s2)

Related: `slot`, `authority`, `freshness`, `producer`, `admission`

## lineage

How an item's body relates to its source: verbatim, summarised, redacted, translated, extracted or model-generated.

> lineage: Verbatim, summarised, redacted, translated, extracted, or model-generated.

Where: [Spec §2.2](https://contextwindowarchitecture.io/spec.html#s2)

Related: `variant`, `item`

## MCP

The Model Context Protocol, a transport for tools and resources. Under CWA an MCP adapter's results become evidence items with freshness and authority, and its tool specifications are proposed to the capability policy, never placed by the adapter itself.

Where: [Spec §3](https://contextwindowarchitecture.io/spec.html#s3)

Related: `producer`, `capability-policy`, `evidence-plane`

## memory

Summaries and inferred facts the system wrote about earlier turns, each linked to its source turn and carrying an expiry: fallible, compressible and revocable. It is not state, which the application writes from its own records.

> Memory is fallible, compressible, linked to its source, and revocable.

Where: [Spec §3.2](https://contextwindowarchitecture.io/spec.html#s3)

Related: `state`, `expires`, `interaction`

## payload

The rendered request the model receives: each item's text in the role its renderer assigns, in the order the profile gives, hashed and counted in the trace. A refused assembly has no payload.

> It hands the payload to the model with each text in the platform role its renderer assigns, text assigned none in a single user message, where the query alone is the live turn, and no text of its own.

Where: [the live assembly](https://contextwindowarchitecture.io/assembler.html#assemble)

Related: `renderer`, `profile`, `trace`, `refusal`

## placement

Where an item sits in the window. It changes whether the model uses the item, and differently for every model family, task and context length, which is why the specification makes placement a profile rather than a rule.

> Placement is model-, task- and content-dependent. This specification takes no position on where items go.

Where: [why placement is a profile](https://contextwindowarchitecture.io/evidence.html#position)

Related: `profile`, `evaluation`

## placement profile

A versioned document that says where each slot goes in the request and how it is wrapped, for one route, and whether that order has been evaluated. CWA fixes what slots mean and leaves where they go to the profile.

> It fixes the semantic slots and requires that placement be a profile: versioned, per route, and evaluated against that route's tasks before it's promoted for deployment (R-19).

Where: [the profile format](https://contextwindowarchitecture.io/evidence.html#format)

Related: `placement`, `route`, `renderer`, `evaluation`

## plane

One of the four groups a slot belongs to, each answering a different question: who may direct the model, what is true right now, what the model may ground on, and what has happened and what is asked.

> Every item belongs to exactly one slot; slots are grouped into four planes. The planes answer four different questions and are never merged.

Where: [the schema](https://contextwindowarchitecture.io/index.html#planes)

Related: `slot`, `governance`, `state`, `evidence-plane`, `interaction`

## producer

Anything that emits candidate items into a slot: a retriever, a memory store, an MCP server, a state service, a capability policy, the application's policy loader, its conversation. A producer hands over one batch per call, items and exclusions together.

> A conformant producer emits only items that meet section 2's rules for an item (R-1, R-2), which admission checks, plus the MUSTs aimed at producers

Where: [Spec §1](https://contextwindowarchitecture.io/spec.html#s1)

Related: `item`, `batch`, `assembler`, `application`, `mcp`, `capability-policy`

## refusal

An assembly that renders no payload because a rule forbids one: a required slot has no item, protected content cannot fit, or a route that requires evidence has none left. The trace still records every decision made before the refusal.

Where: [Spec R-17](https://contextwindowarchitecture.io/spec.html#R-17)

Related: `rejection`, `trace`, `tier`, `budget`

## rejection

What happens to a snapshot that fails its schemas or checks: it is rejected before assembly, with neither a payload nor a trace. Rejection is about the input's shape; refusal is a decision about valid input.

Where: [Spec R-17](https://contextwindowarchitecture.io/spec.html#R-17)

Related: `refusal`, `snapshot`, `conformance-case`

## renderer

The published procedure that writes the request from the fitted items in the profile's order and assigns each text its platform role. The specification publishes fixture-xml/v1 and cwa-messages/v1, and cwa-message-blocks/v1 as an option.

> Profiles place slots and pick their wrappers, a published renderer writes the request from them, and wire encodings must preserve these semantics.

Where: [Spec §1](https://contextwindowarchitecture.io/spec.html#s1)

Related: `payload`, `profile`, `tokenizer`

## requirement

One numbered rule of the specification, R-1 onward. Numbers are permanent: a withdrawn rule keeps its number and a new rule takes the next one, whatever section it lands in.

> Requirements are numbered R-n in a single flat sequence. A number is assigned once and never reused.

Where: [the requirement index](https://contextwindowarchitecture.io/spec.html#index)

Related: `conformance`

## route

One kind of request an application serves, such as support chat, code review or a weekly brief. Each route has a versioned route policy and a placement profile of its own.

Where: [Spec §5](https://contextwindowarchitecture.io/spec.html#s5)

Related: `route-policy`, `profile`

## route policy

The route's versioned rules: which producers it lists, with their kinds and slots; each slot's eligibility rules, caps and floors; the fitting order; and, for each fact, which producer's claim takes precedence.

> route policy for the group's fact key lists the eligible producers, by authenticated identity, in precedence order, and the scope keys a claim must carry.

Where: [Spec §3.3](https://contextwindowarchitecture.io/spec.html#s3)

Related: `route`, `producer`, `admission`, `conflict-group`, `tier`

## rule zero

Language guidance goes in context; enforceable invariants go outside the model. A governance item may say never quote an unverified price, and a tool guard still enforces it, because no assembler relies on context to keep an invariant.

> An assembler MUST NOT rely on context to enforce an invariant.

Where: [Spec R-5](https://contextwindowarchitecture.io/spec.html#R-5)

Related: `governance`, `application`

## scope

The tenant, user, session, task, locale or workflow step an item applies to. An item outside the request's scope never reaches the payload.

> scope: Tenant, user, session, task, locale, workflow step. Out-of-scope items never reach the payload.

Where: [Spec §2.2](https://contextwindowarchitecture.io/spec.html#s2)

Related: `admission`, `item`

## slot

A typed collection inside a plane, with its own admission rules and defaults. There are eleven, such as governance.instructions, evidence.knowledge and interaction.query, and every item names exactly one.

> Every item MUST name exactly one slot and one authority value from the closed set in section 3.

Where: [Spec §2.1](https://contextwindowarchitecture.io/spec.html#s2)

Related: `plane`, `item`, `admission`, `tier`

## snapshot

Everything one model call depends on, frozen before assembly: the producers' batches, the capability grant, the conflict groups, the scope, the assembly time, the route policy, the profile, the tokenizer, the renderer and the budget. The same snapshot renders the same bytes every time, so a stored one replays.

> makes every external read, retrieval and model call before it freezes the snapshot, and freezes a new one for any retry (R-12, R-23)

Where: [Spec R-23](https://contextwindowarchitecture.io/spec.html#R-23)

Related: `assembler`, `payload`, `trace`, `rejection`, `batch`

## source diversity

A route option on a slot: at most a set number of items per producer and source, so that one document cannot fill the slot. The rest are excluded as source_diversity_cap.

Where: [Spec R-26](https://contextwindowarchitecture.io/spec.html#R-26)

Related: `deduplication`, `supersession`

## state

The plane that holds what is true right now: facts about the user and the task, written by the application from its database or workflow engine and never inferred from the conversation. The database is the source of truth, not the model.

> State is canonical, structured, typed, current, and owned by the application.

Where: [Spec §3.2](https://contextwindowarchitecture.io/spec.html#s3)

Related: `plane`, `memory`

## supersession

A route option on a slot. When the same producer sent several observations with the same source, only the newest survives, and the older ones are excluded as superseded.

Where: [Spec R-25](https://contextwindowarchitecture.io/spec.html#R-25)

Related: `freshness`, `deduplication`, `source-diversity`

## tier

A slot's standing under budget pressure. Protected items are rendered whole or the assembly is refused; compressible items may be swapped for a shorter variant or omitted; droppable items may be omitted, and go first.

> Every slot sits in one of three tiers. Protected items are rendered whole or the assembly is refused. Droppable items may be omitted. Compressible items may be replaced by a precomputed shorter variant or omitted.

Where: [Spec §4.1](https://contextwindowarchitecture.io/spec.html#s4)

Related: `budget`, `variant`, `refusal`, `slot`

## tokenizer

How tokens are counted for fitting. The specification publishes two, fixture-whitespace/v1 for its tests and estimate-utf8/v1 for estimates; an application may count with its own, under an unused ID, paired with a margin that covers its error.

> It declares a tokenizer that reads nothing but the text it counts (R-23) and counts the model's tokens, or estimates them with a budget.margin_percent that covers the error for the route's text (R-16)

Where: [Spec R-16](https://contextwindowarchitecture.io/spec.html#R-16)

Related: `budget`, `renderer`

## trace

The record every assembly emits: what was included, compressed and excluded and why, each declared conflict and how it was decided, the profile and budget used, and the payload's token count and hash. A refused assembly still has a trace.

> Every assembly emits a trace.

Where: [Spec §6](https://contextwindowarchitecture.io/spec.html#s6)

Related: `payload`, `exclusion`, `refusal`, `conformance`

## trust

The producer's own claim about its source: verified, unverified or untrusted. Only the governance gate reads it, which admits verified items alone; it never decides who may instruct or which fact wins.

> Among admitted items, trust and injection_risk never change which items may; they act only at admission (R-10).

Where: [Spec §2](https://contextwindowarchitecture.io/spec.html#s2)

Related: `authority`, `injection-risk`, `admission`

## variant

A shorter version of an item that its producer computed before assembly, with its own id, body, method and lineage. Fitting may swap one in for a compressible item; the assembler never writes its own.

> variants: Shorter versions the producer computed ahead of time, each with its own id, body, method and lineage.

Where: [Spec R-18](https://contextwindowarchitecture.io/spec.html#R-18)

Related: `tier`, `lineage`, `producer`
