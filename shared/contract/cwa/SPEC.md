# Context Window Architecture: specification

Draft of 2026-10-07, not yet stable. Requirements are numbered from R-1; new ones append, and numbers are permanent and never reused.

This file is the normative text of the specification. The [Spec page](https://contextwindowarchitecture.io/spec.html) renders it; where the page differs from this file, this file holds. [CHANGES.md](CHANGES.md) lists every revision.

The requirement index, each section's requirements, the lists of planes, slots, item fields, authority values, conflict rules, stages and tests, and the profile example are written from [contract/requirements.json](contract/requirements.json), [contract/model.json](contract/model.json) and [examples/profiles.json](examples/profiles.json) by `python3 conformance/check.py --write`. Edit those files, not the text between `generated` markers.

## Requirement index

<!-- generated:index -->

| Requirement | Keyword | Summary |
| --- | --- | --- |
| R-1 | MUST | One slot and one authority role per item |
| R-2 | MUST | Required fields and canonical JSON shape |
| R-3 | SHOULD | Declared policy defaults, filled and traced |
| R-4 | MUST | Slots that are never omitted |
| R-5 | MUST NOT | Rule zero: enforce outside the model |
| R-6 | MUST | Separate instruction authority from factual precedence |
| R-7 | MUST NOT | No slot overrides platform roles; no authority from wording |
| R-8 | MUST | State is application-written and current |
| R-9 | MUST | Memory lifetime and producer exclusion reporting |
| R-10 | MUST | User and fetched content is marked, never elevated, kept out of governance |
| R-11 | MUST | Explicit conflict groups and traceable resolution |
| R-12 | MUST NOT | Never answer from nothing |
| R-13 | MUST NOT | Retrievers emit one scored item per chunk, never a blob |
| R-14 | MUST NOT | Memory producers suppress and report expired or revoked items |
| R-15 | MUST | Authenticated capability admission; MCP output is evidence |
| R-16 | MUST | Account for rendered tokens; shed in tier order |
| R-17 | MUST | Refused assembly has no rendered payload |
| R-18 | MUST NOT | Precomputed variants; no model calls during assembly |
| R-19 | MUST | Draft profiles versus evaluated profiles |
| R-20 | MUST | Profile version and mandatory-slot validation |
| R-21 | MUST | Trace JSON matches the published schema |
| R-22 | MUST | Provenance, snapshot digest and filled defaults in the trace |
| R-23 | MUST | Determinism includes the clock and policy snapshot |
| R-24 | MUST | Route-requested exact deduplication |
| R-25 | MUST | Route-requested supersession of stale observations |
| R-26 | MUST | Route-requested source diversity |

<!-- /generated:index -->

## 1 Conformance

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in RFC 2119. MUST is required for conformance; SHOULD is expected unless a reason is recorded; MAY is optional.

A **conformant assembler** meets every MUST an assembler can meet by itself, provides every tokenizer and renderer that Tokenizers and renderers in conformance/README.md requires, and can emit its trace as JSON with the fields R-21 lists. A **conformant producer** emits only items that meet section 2's rules for an item (R-1, R-2), which admission checks, plus the MUSTs aimed at producers: every producer reports each entry it suppresses (R-9) and computes its scores and variants before assembly (R-18), and, by kind, R-9 and R-14 bind memory, R-10 anything carrying user-controlled or fetched content, R-13 retrievers, R-15 MCP adapters, and R-18's variant rules anything that supplies variants. A **conformant application** uses a conformant assembler and only conformant producers, and meets the MUSTs no component can meet for it: it enforces invariants, tool permissions among them, outside the model (R-5, R-15), writes state (R-8), declares conflict groups (R-11), authenticates each producer and binds its identity outside the items (R-15), makes every external read, retrieval and model call before it freezes the snapshot, and freezes a new one for any retry (R-12, R-23), sets parser: true on every route whose response a downstream parser consumes (R-4), sets budget.input to the model's context limit less budget.reserved_output (R-16), versions its profiles (R-20) and deploys only evaluated ones (R-19). It renders with a renderer the published cases cover. It declares a tokenizer that reads nothing but the text it counts (R-23) and counts the model's tokens, or estimates them with a budget.margin_percent that covers the error for the route's text (R-16); the tokenizer may be its own, under an ID no published tokenizer uses. It hands the payload to the model with each text in the platform role its renderer assigns, text assigned none in a single user message, where the query alone is the live turn, and no text of its own. Request structure the renderer leaves to it, such as a provider's cache breakpoints, cache lifetime or cache key, adds no text, so the count and hash its trace records still describe what the model reads. The roles R-7 has the assembler assign, and the count R-16 has it make, hold for the payload it renders, as its report shows; only this handoff makes them hold for what the model receives. The [Assembler page](https://contextwindowarchitecture.io/assembler.html) marks each requirement as assembler, boundary or application, so you can see who owns which part.

These are the only claims this specification defines. An application is not conformant because one of its parts is, though it may say which of its parts are. The claims also differ in kind. Producer and application conformance is an agreement about what each emits and does. Assembly cannot confirm all of it, so the claim rests on their word, and an assembler's boundary checks catch only some breaches. An assembler's conformance concerns what it decides. A wrong decision fails silently, because a model accepts any payload, so the claim rests on evidence: a conformance report showing that the assembler passes every published case and rejects every published rejection, skipping only those that use an optional tokenizer or renderer it does not provide, as Reporting results in conformance/README.md describes. An application's claim includes its assembler's, which is why it must render with a renderer the published cases cover: that assembler's report then backs how the payload is built. Its tokenizer need not be one the cases cover: they test how an assembler applies a tokenizer's counts, and no case can test whether those counts match a model only the application calls. That, and the handoff to the model, rest on the application's word like the rest of its claim.

Requirements are numbered R-n in a single flat sequence. A number is assigned once and never reused. A withdrawn requirement keeps its number and is marked withdrawn in the index. Other pages on this site, and the reference implementation, cite requirements by number.

The published JSON Schemas define item and trace field shapes. Profiles place slots and pick their wrappers, a published renderer writes the request from them, and wire encodings must preserve these semantics. The website tools check structure and selected local invariants, not full implementation conformance.

## 2 Model: planes, slots, items

A model call is assembled from **items**. Every item belongs to exactly one **slot**; slots are grouped into four **planes**. The planes answer four different questions and are never merged. An item in one of the two evidence slots is an **evidence item**, and the piece of a document a retriever pulls is a **chunk**.

<!-- generated:planes -->

| Plane | Answers | Slots |
| --- | --- | --- |
| Governance | Who may direct the model | `governance.instructions`, `governance.capabilities`, `governance.examples`, `governance.output_contract` |
| State | What is true right now | `state.user`, `state.task` |
| Evidence | What the model may ground on | `evidence.knowledge`, `evidence.tool_results` |
| Interaction | What has happened, and what is asked | `interaction.memory`, `interaction.history`, `interaction.query` |

<!-- /generated:planes -->

### 2.1 Slots

<!-- generated:slots -->

- `governance.instructions`: Identity, goals, refusals, and safety boundaries: the system's constitution. This slot is never omitted and admits only governing-authority items. Items that aren't verified, or that carry the injection marker, are excluded here.
- `state.user`: Durable profile, entitlements, locale, permissions, session preferences, each a separate item with its own freshness. Items are scoped to the current tenant and user. Unverified user claims remain source-linked memory; only application-confirmed facts enter state.
- `evidence.knowledge`: Retrieved chunks, each sent as its own evidence item with source, version, relevance and trust. Each one has to clear admission: a relevance score at or above the route's min_relevance, and inside its freshness limits. Where the route asks for it, exact duplicates go after conflicts are resolved (R-24). An empty result is recorded as an outcome, not treated as an error.
- `state.task`: Workflow stage, approval status, selected entity IDs, pending action, retry count. Task state is written by the application's state machine and never inferred from conversation.
- `interaction.memory`: Condensed summaries of older turns and inferred long-term facts, each linked to the turn it came from. Every entry carries an expires deadline and a source naming the turn it came from. Entries whose expires is at or before assembly_time, or that carry revoked_by, are excluded and show up in the trace (R-9). The assembler doesn't decide what's been contradicted; the application revokes it.
- `interaction.history`: A verbatim transcript of the most recent turns, bounded by turn count and tokens. Before assembly, overflow gets summarised into memory rather than cut mid-thought. Under budget pressure, when the route declares no fitting order, turns with a shorter variant switch to it first; after that, whole turns are dropped, oldest first unless the turns carry relevance scores or the route ranks the slot differently. Prior model turns carry lineage: generated and untrusted authority, and every prior turn renders inside the history transcript, never as a platform message. Turns render in the order they were said: by freshness, then id (R-7).
- `governance.capabilities`: The tools, functions and resources the model is permitted to invoke, with their contracts. Only tools the route's capability policy allows for this user are admitted, against a versioned allow-list. Permission is decided outside the model.
- `evidence.tool_results`: Observations returned by tools already called, possibly several per loop, and any retrieved chunks a route sends here. When the route sets supersede: source, the newest observation from each producer and source stays and the older ones go (R-25). That's keyed on source, not on the tool call. An observation is evidence, not permission to act.
- `governance.examples`: Developer-owned input/output pairs that steer reasoning, tone or format, ranked by task similarity. A route that wants them places the slot and lists a producer for it; admission applies the same four slot rules as anywhere else (R-3). They defer to instructions and the output contract. They're droppable, so under budget pressure they go before anything compressible.
- `governance.output_contract`: Structure, style, length and schema of the response about to be generated. The contract is never omitted when a downstream parser exists. If a safety disclosure has to appear, make room for it in the contract itself. Conflict resolution can't drop a protected item, so a clash between the two escalates.
- `interaction.query`: The most recent, unprocessed input the model must respond to. The query is never omitted and always carries user authority. It is the trigger for generation, placed wherever the route's profile puts it.

<!-- /generated:slots -->

### 2.2 Item fields

Eight fields are the minimum an assembler needs to place, rank, expire and trace an item. Six more carry the item's policy; when a producer omits them the assembler fills them from the slot's defaults. The JSON Schema is published with the scaffold.

**Minimum · MUST**

<!-- generated:mustFields -->

`id`, `slot`, `source`, `source_version`, `authority`, `freshness`, `trust`, `body`

<!-- /generated:mustFields -->

**Policy · SHOULD**

<!-- generated:shouldFields -->

`token_budget`, `variants`, `conflict_policy`, `lineage`, `eligibility`, `injection_risk`

<!-- /generated:shouldFields -->

<!-- generated:itemFields -->

- **provenance**: source and source_version: which document, turn, tool call, database field or memory write it came from, and which version.
- **authority**: Exactly one of the seven roles in section 3.1: governing instruction, user intent, state, reference evidence, observation, generated memory, or untrusted. Each slot takes its own role; tool results, memory and history may take untrusted instead (R-1). Only governing and user can instruct. No other value is valid.
- **freshness**: freshness records when content was observed or true; expires is the separate expiration deadline. as_of is prose, not a JSON alias.
- **scope**: Tenant, user, session, task, locale, workflow step. Out-of-scope items never reach the payload.
- **eligibility**: A short note on why this item belongs in the request, for whoever reads the trace. It isn't code; the route owns the rule that actually decides (R-3).
- **budget**: token_budget and tier: how much it may consume, which tier it sits in, and what shortens first under pressure.
- **conflict_policy**: What wins if another item disagrees: this one defers, governs, or forces escalation. Applied only to permitted instruction peers; factual precedence belongs to route policy.
- **lineage**: Verbatim, summarised, redacted, translated, extracted, or model-generated.
- **trust**: Verified, unverified, or untrusted: the producer's own claim about its source, so it proves nothing (R-15). Only the governance gate reads it, which admits verified items alone (R-10). It never decides who can instruct or which fact wins.
- **variants**: Shorter versions the producer computed ahead of time, each with its own id, body, method and lineage. Fitting can swap one in but never writes its own (R-18).
- **injection_risk**: untrusted_content when the body might carry an injection, whatever its authority. A retrieved chunk is reference_only in knowledge and observation in tool results, and untrusted_content in both (R-10). The marker never changes authority or where an item renders: a query or history turn keeps user authority although marked, and material pasted into its body renders with it, because the assembler never splits a body.

<!-- /generated:itemFields -->

<!-- generated:rulesModel -->

### R-1: One slot and one authority role per item

Every item MUST name exactly one slot and one authority value from the closed set in section 3.1. Governing slots MUST carry governing; state slots state; knowledge reference_only; tool results observation; memory generated; history and query user, with two exceptions: prior model turns in history, marked lineage: generated, MUST carry untrusted, and any other item in evidence.tool_results, interaction.memory or interaction.history MAY carry untrusted instead. An item whose slot is not one of the eleven, whatever its JSON type, MUST be excluded with unknown_slot, one whose authority is outside the set, whatever its JSON type, with unknown_authority, and one whose authority is in the set but not permitted for its slot with authority_not_allowed. untrusted only keeps an item out of an instruction group's peers, so that group neither lets it prevail nor excludes it (R-6, R-11); a fact group ranks it like any other member, and every other rule of its slot still applies. These values classify instruction authority or data provenance; they MUST NOT form a global factual ranking.

### R-2: Required fields and canonical JSON shape

Every item MUST carry id, slot, source, source_version, authority, freshness, trust and body and MUST satisfy the published context_item.schema.json. freshness is an RFC 3339 date-time recording when the fact was observed or true; it is not an expiration time. expires is a separate deadline: an item whose expires is at or before assembly_time is expired (R-9). as_of is explanatory terminology, not a JSON alias. An item with invalid structure MUST be excluded and recorded: with missing_field:\<name> when a required field of the item itself is absent, and otherwise with invalid_structure. A batch entry that is not a JSON object is not an item: the snapshot holding it fails its published schema and is rejected (R-17). An item MUST be excluded with duplicate_item_id when another candidate or producer exclusion in the snapshot uses its id. An item MUST be excluded as out_of_scope when a scope key it carries has a value other than the request's, including a key the request lacks, or when it lacks a key its slot's required_scope lists; a missing key is never a wildcard. An item whose freshness is later than assembly_time by more than the route's clock_skew_seconds MUST be excluded with future_freshness. An item without a non-blank string id MUST be recorded as {producer id}#invalid-{n}, where n counts such items from 0 in the order their batch supplied them. Assemblers and validators MUST compare timestamps as instants at their full stated precision and MUST NOT truncate fractional seconds. Every number in a snapshot is an IEEE 754 double (I-JSON): an assembler MUST read each number as the nearest double before comparing it with anything, so an integer beyond 2^53 compares in every language as the double it rounds to, which is the value the snapshot digest serializes (R-22).

### R-3: Declared policy defaults, filled and traced

An item SHOULD carry token_budget, variants, conflict_policy, lineage, eligibility and injection_risk. When omitted, the assembler MUST apply the defaults published in contract/slot-defaults.json, with any route overrides versioned and recorded, and MUST trace every filled field. variants defaults to an empty list; token_budget caps the tokens of the item's rendered body; null sets no per-item cap, and budget.input and any max_tokens the route sets for the item's slot still bound it. eligibility is descriptive text, not executable code; the route's versioned slot rules are the executable eligibility predicate. The slot-level eligibility rules min_relevance (R-13), max_age_seconds, required_scope (R-2) and source_prefix are the complete set: an assembler MUST NOT apply any other eligibility rule, while every other admission check, such as producer authentication (R-15), still applies. An item observed longer ago than its slot's max_age_seconds MUST be excluded, as stale_state in a state slot (R-8) and as not_eligible elsewhere, and an item whose source does not start with its slot's source_prefix MUST be excluded with source_invalid. conflict_policy applies only among the peers of an instruction group (R-11) and is ignored for factual precedence.

### R-4: Slots that are never omitted

governance.instructions and interaction.query MUST NOT be omitted from any assembly. governance.output_contract MUST NOT be omitted when a downstream parser consumes the response, which the route policy declares with parser: true. When one of these slots has no admitted item, the assembler MUST refuse with required_slot_missing (R-17).

<!-- /generated:rulesModel -->

## 3 Governance

**Rule zero**

Language guidance goes in context, and enforceable invariants go outside the model. "Never quote an unverified price" is stated in governance and enforced by a tool guard: the model is instructed, but the application still enforces the rule.

### 3.1 Instruction authority and data roles

<!-- generated:authority -->

| Role | Authority | Meaning |
| --- | --- | --- |
| Governing instruction | `governing` | System and developer policy, safety constraints, the output contract, admitted capabilities, and steering examples. |
| User intent / preference | `user` | What the user asks for and how they want it. It cannot lift a constraint set above it. |
| Canonical state | `state` | Application-owned facts about the task and session. The route defines the facts for which this source is canonical. |
| Reference evidence | `reference_only` | Retrieved chunks in knowledge, which inform the answer but never direct behaviour. |
| Tool observation | `observation` | What a tool returned, and any retrieved chunk a route sends to tool results: evidence about the world, not permission to act on it. |
| Generated memory | `generated` | Summaries and inferences the system wrote. They are fallible, they expire, and they can be revoked. |
| Untrusted (least privilege) | `untrusted` | Prior model turns in history, which must carry it, and any other item in tool results, memory or history whose producer wants it handled with the least privilege. It keeps the item out of an instruction group's peers and changes nothing else. Governance, knowledge, state and the query never carry it. Not the same as injection_risk: untrusted_content, which flags content that might carry an injection. |

<!-- /generated:authority -->

These seven values are the complete set, and the monospaced one under each name is what goes in the authority field. Only governing and user items can direct behavior: governing instructions, the live query, and the user's own earlier turns in history. Prior model turns carry untrusted, so they can't. Authority alone decides this: an item's trust and injection_risk never add or remove it (R-6). The other five values say where data came from. They aren't a ranking of which facts are true. An item with any other authority value is excluded at admission.

Slots never override platform message roles or application controls. A retrieved document is not an instruction because it contains imperatives. A preference does not lift a safety constraint. Tool output is evidence, not permission to act.

### 3.2 State is not memory

**state.\***

State is canonical, structured, typed, current, and owned by the application. It holds workflow stage, approval status, selected entity IDs, pending action, and retry count. The database is the source of truth, never the model.

**interaction.memory**

Memory is fallible, compressible, linked to its source, and revocable. It holds preferences, prior-discussion summaries, and inferred long-term facts. Every entry carries an expires deadline and the turn it came from.

### 3.3 Conflict resolution · instruction rules and factual route policy

<!-- generated:conflicts -->

| When | Then |
| --- | --- |
| System or developer policy vs user request | Higher-authority policy governs. |
| Fresh verified tool output vs retrieved document | The route may prefer the verified observation for the same current fact by listing its producer first; trust is never read, and unresolved conflicts escalate. |
| Canonical task state vs conversational recollection | The route selects current application state for its owned facts; the model never writes that state. |
| User correction vs inferred memory | The application processes the correction and explicitly revokes affected memory; the trace records the exclusion. |
| Conflicting retrieved sources | The route's fact policy picks by producer precedence, and the loser shows up as conflict_lost. If it can't pick, the conflict is surfaced, more context is requested, or the assembly is refused. |
| Format constraint vs required safety disclosure | Both are governing and protected, so if you group them the conflict escalates. Write the disclosure into the contract so they never collide. |
| Steering example vs instruction or output contract | The instruction or contract governs. Examples defer to other governing items. |

<!-- /generated:conflicts -->

**Instruction conflicts:** platform roles and application controls first, governing instructions over user requests, then the peers' own conflict policies. The peers are the members at the highest authority in the group that can instruct: governing, or user if no governing item is there. A group left with fewer than two admitted members is moot. Otherwise, a group with one peer or none is decided by authority, and nothing is excluded. If exactly one of two or more peers says governs and the rest say defers, the deferring ones are excluded. Items with any other authority, which covers every state, evidence and memory item and anything carrying untrusted, never become instructions, whatever their wording; they stay as material. Anything else escalates to the route's on_unresolved_instruction action.

**Factual conflicts:** route policy for the group's fact key lists the eligible producers, by authenticated identity, in precedence order, and the scope keys a claim must carry. It may prefer a verified current observation over a stale document by listing that producer first, but no data role automatically wins, and an item's trust, its injection marker and the route's verified flag are never read (R-11). Freshness breaks a tie only between leaders from the top-ranked producer, and only when the route permits it, so it never lets an ineligible claim win; otherwise the route surfaces the conflict, requests more context or refuses. No conflict excludes a protected item. The application supplies typed conflict groups; the assembler does not discover contradictions by interpreting prose.

<!-- generated:rulesGov -->

### R-5: Rule zero: enforce outside the model

An assembler MUST NOT rely on context to enforce an invariant. Governance items MAY state a rule; the application MUST enforce it outside the model.

### R-6: Separate instruction authority from factual precedence

An assembler MUST classify supplied conflict groups as instruction or fact before resolution. For instructions, platform message roles and application controls govern first; governing instructions outrank user requests. Only items whose authority is governing or user may issue behavioral instructions; items with any other authority, which include every state, evidence and memory item (R-1), MUST NOT. Among admitted items, trust and injection_risk never change which items may; they act only at admission (R-10). For facts, an assembler MUST use explicit, versioned route policy over the same fact and scope, MUST NOT use authority values as a truth ranking, and MUST escalate if policy cannot establish precedence.

### R-7: No slot overrides platform roles; no authority from wording

An assembler MUST NOT let any slot override platform message roles or application controls. An item MUST NOT gain authority from imperative wording in its body. Prior turns in interaction.history MUST render inside the profile's history wrapper as a transcript, in the order they were said: by freshness, which for a turn records when it was said (R-2), compared as instants at full precision, and by id among turns said at the same instant. They never render as platform user or assistant messages; only interaction.query renders as the live user turn.

### R-8: State is application-written and current

state.\* items MUST be written by the application and MUST be current at assembly time: a state item observed longer ago than its slot's max_age_seconds MUST be excluded with stale_state (R-3). An assembler MUST admit state items only from producers of kind state, whatever else a route policy lists. An assembler MUST NOT write state from model output.

### R-9: Memory lifetime and producer exclusion reporting

interaction.memory items MUST carry expires and a source identifying the source turn. Any item expired at assembly_time, that is, whose expires is at or before it, MUST be excluded with expired, and any item carrying revoked_by with revoked, memory or not. Producers MUST report suppressed entries as excluded records containing item_id, reason and stage: producer, with reason one of the exclusion codes in contract/reasons.json; a record with reason superseded MUST carry superseded_by naming a candidate in the same batch, as R-13 requires duplicate_of; the assembler MUST merge those records into its trace, including those from a batch whose producer the route does not admit. Expiration MUST use the explicit assembly_time snapshot, not an ambient clock.

### R-10: User and fetched content is marked, never elevated, kept out of governance

User-controlled quoted material, attachments, retrieved chunks, memory and tool output MUST be marked injection_risk: untrusted_content, except output from an MCP server the route policy verifies (R-15), and, when supplied as items of their own, rendered inside their slot's wrapper, never in a platform system or tool role (R-7). An assembler MUST exclude with untrusted_content_unmarked any item that is not so marked, as given or as filled (R-3), in a slot whose published injection_risk default is untrusted_content, unless that exception applies. The marker never changes authority (R-6): the interaction.query item carries user authority (R-1) and keeps it although it is marked, as do user turns in history. Material pasted or attached into the body of a query or history item renders with that body, since assembly never splits a body, and gains no instruction authority from the item; its marking does not change what the model sees, so an application SHOULD delimit such material inside the body in a form the material cannot imitate. An assembler MUST exclude with untrusted_in_governance any governance item whose trust is not verified or that is marked untrusted_content. Only an authenticated route policy may grant the verified-MCP exception in R-15.

### R-11: Explicit conflict groups and traceable resolution

The application MUST supply conflict groups satisfying schema/conflict_group.schema.json: a group id unique in the snapshot, kind: instruction or fact, the IDs of candidates or producer exclusions in the snapshot, each in at most one group, and, for fact groups, a fact key that the route policy defines; assembly MUST NOT infer semantic contradictions by calling a model. A group left with fewer than two admitted members is moot and excludes nothing; the rules below decide every other group. Instruction conflicts follow platform roles, governing over user, then conflict_policy for permitted peers: resolving authority excludes nothing, and members that cannot instruct (R-6) remain as material. An instruction group's peers are its members at the highest authority present among those that may instruct: governing, or else user. With one peer or none, authority decides the group and nothing is excluded. With two or more, when exactly one governs and the rest defer, the assembler MUST exclude the deferring peers with reason conflict_deferred; any other pattern escalates. Factual conflicts use the route policy for that fact key, which lists eligible producers by authenticated identity in precedence order, the scope keys members must carry and any freshness tie-break. A member is eligible exactly when its producer is listed and it carries those scope keys. The leaders are the eligible members whose producer ranks first, so they all come from one producer; a single leader wins by policy, and a freshness tie-break, when the policy sets one, decides only among several leaders, so freshness never makes an ineligible member win. A member's trust and injection_risk, and the route's producers.\<id>.verified flag, are not consulted; a route that prefers a verified source lists its producer earlier. When a member of a fact group wins, every other member is excluded with reason conflict_lost. Conflict resolution MUST NOT exclude a protected item; such a group escalates. The trace MUST hold one conflict record per declared group, recording group_id, kind, items, resolution and decided_by: authority, policy, freshness, escalated or moot, and, when one member prevails, winner. policy means the peers' conflict_policy for instruction groups and the route's fact policy for fact groups. authority MUST NOT decide a factual conflict. moot records a group left with fewer than two admitted items and MUST NOT be used while two or more remain. A group lacking a unique supported resolution MUST be surfaced, routed for more context or refused as route policy directs, never silently discarded; a surfaced group's members are marked as conflicting in the payload. Fitting may still omit a surfaced member under R-16; its over_budget row records the omission, and the members kept stay marked. When assembly refuses with conflict_unresolved and every group that caused it asked for more context, the trace MUST record recovery.action: request_context.

<!-- /generated:rulesGov -->

## 4 Admission & fitting

Evidence goes through eight steps between the source and the payload. The first four are the producer's, and they're done before assembly starts. The last four are the assembler's, and everything it leaves out shows up in the trace with a reason code.

<!-- generated:stages -->

1. **Rewrite**: Decide whether to rewrite the query for retrieval, and keep the rewritten form so you can explain the results later.
2. **Retrieve**: Pull candidate chunks from sources whose provenance you can name.
3. **Rerank**: Score each candidate against the query and put the score in relevance. If you drop a near-duplicate, report it as duplicate_content, with duplicate_of naming the one you kept (R-13).
4. **Package**: Send each chunk as its own evidence item with source, source_version, relevance and the authority its evidence slot takes (R-1). Never one merged blob (R-13).
5. **Admit**: Check each item against its schema and the route: who sent it, which slot, what authority, its scope, age and expiry, and the route's min_relevance. Anything that fails is excluded with a reason code.
6. **Resolve**: Settle the conflict groups the application declared (R-11). Then, in the slots where the route asks, drop superseded observations (R-25), exact duplicates (R-24) and anything past max_per_source (R-26), in that order.
7. **Fit**: Refuse before any reduction if protected content can't fit (R-16, R-17). Otherwise apply item and slot caps, then shed in tier order under budget pressure: droppable first, then compressible (R-16). If too little evidence is left on a route that requires it, refuse instead (R-12).
8. **Render & trace**: Render the payload in the profile's order, hash it, and write a trace that accounts for every decision above (R-21).

<!-- /generated:stages -->

### 4.1 Budget tiers

Every slot sits in one of three tiers. Protected items are rendered whole or the assembly is refused. Droppable items may be omitted. Compressible items may be replaced by a precomputed shorter variant or omitted. Under budget pressure that happens only once droppable items are gone; the route's versioned fitting policy orders that step, and without one, variants come before omission. The one exception is a slot the route holds at a min_tokens floor: it can keep its droppable items while other slots compress. An item over its own token_budget, or in a slot over the route's max_tokens, is reduced first, whether or not the payload fits. Every omission is traced as over_budget. The assembler never touches protected items. Only the route's versioned policy can raise a slot's tier; an item that claims a higher tier than its slot allows is excluded with tier_upgrade_not_allowed, so a producer cannot protect its own items.

<!-- generated:rulesFit -->

### R-12: Never answer from nothing

When admission and fitting leave no valid evidence, or fewer items in an evidence slot than that slot's versioned min_included, for a route that requires evidence, an assembler MUST NOT render a payload as though sufficient evidence were present. It MUST emit a refusal with reason evidence_required and record recovery.action: request_context when no evidence item was omitted for budget, precompute_summary when one that was had no variants, and retrieve_narrower otherwise. An evidence item was omitted for budget when its exclusion is recorded with reason over_budget, whether for the payload budget, its own token_budget or its slot's max_tokens (R-16). Retrieval or model-based summarization MUST occur outside assembly; any retry MUST create a new immutable snapshot.

### R-13: Retrievers emit one scored item per chunk, never a blob

A retrieval producer MUST NOT emit a merged blob. Each candidate MUST be a separate item in evidence.knowledge or evidence.tool_results, carrying the authority R-1 permits in that slot and its rerank score as relevance; an assembler MUST exclude with producer_slot_not_allowed any item a producer of kind retrieval sends to any other slot, whatever the route lists. Every evidence.knowledge item, from any producer, MUST carry relevance, and one without it is excluded with missing_field:relevance (R-2). An assembler MUST exclude with below_threshold an item scoring below its slot's min_relevance, or carrying no score in any other slot that sets one; a score equal to the threshold passes. A retrieval producer that drops a candidate as a near-duplicate of another MUST report it in its batch's excluded list with reason duplicate_content, stage producer and duplicate_of naming the candidate it kept, which MUST be a candidate in the same batch.

### R-14: Memory producers suppress and report expired or revoked items

A memory producer MUST emit only generated or untrusted memory items, and an assembler MUST exclude with producer_slot_not_allowed any item a producer of kind memory sends to a slot other than interaction.memory, whatever the route lists. It MUST NOT emit expired or revoked entries as candidate items. It MUST report them in its producer-batch excluded list with reason expired or revoked and stage: producer, so R-9 can be satisfied without re-emitting their bodies.

### R-15: Authenticated capability admission; MCP output is evidence

MCP results and resources MUST be marked injection_risk: untrusted_content unless the route policy verifies that server. They MUST enter evidence slots, never governance: an assembler MUST exclude with producer_slot_not_allowed any item a producer of kind mcp sends to a slot other than evidence.knowledge, evidence.tool_results or governance.capabilities, whatever the route lists, and a tool specification it sends to governance.capabilities, where the route lists that slot for it, is excluded with capability_not_allowed. Adapters MAY propose tool specifications to the route capability policy. Only that authenticated application policy may emit governance.capabilities with authority: governing, trust: verified and injection_risk: none, after checking the versioned allow-list for the route and user. The application MUST bind producer identity outside item-controlled fields, and a snapshot MUST hold at most one batch per producer; items from a producer the route does not list, or lists with another kind, MUST be excluded with producer_not_authenticated, and an item in a slot the route does not list for its producer with producer_slot_not_allowed; a source prefix or self-declared trust MUST NOT prove authorization. A governance.capabilities item is authorized only when the snapshot carries a capability grant, its batch comes from the producer the grant names as policy_producer, the route lists that producer with kind capability_policy, and the grant's allow-list names the item's id; any other governance.capabilities item MUST be excluded with reason capability_not_allowed. Tool guards MUST still enforce invocation permissions.

### R-16: Account for rendered tokens; shed in tier order

budget.input MUST be the maximum rendered input tokens after reserving budget.reserved_output from the model context limit. The assembler MUST count everything the renderer emits as text, including profile wrappers, separators, tool schemas and repeated slots, with the declared tokenizer. An assembler MUST NOT accept a tokenizer the application supplies under the ID of a published tokenizer, or a renderer under the ID of a published renderer (conformance/README.md, Tokenizers and renderers): it stops before assembly, with no payload and no trace, so a trace that names a published tokenizer or renderer always means its published count or rendering. Structure a renderer does not emit as text, such as a message request's roles, is outside the count, and the route covers it with budget.margin_percent. budget.margin_percent MAY reserve a safety margin for a tokenizer that estimates: the payload then fits only when its token count times (100 + margin_percent) / 100, rounded up, is at most budget.input, and the trace's budget MUST repeat it. Token caps, slot caps and floors, and traced token counts are not scaled by the margin. Under budget pressure it MUST shed in tier order: it MUST omit droppable items before reducing any compressible item, except droppable items a slot floor holds, and it MAY then reduce compressible items by selecting supplied variants or by omitting items, in the order given by the route's versioned fitting policy with a stable tie-break. When the route declares no order, the assembler MUST select variants before omitting any compressible item. It MUST NOT compress, truncate or omit protected items. Before any reduction, the assembler MUST refuse with protected_content_over_budget when a protected item's rendered body exceeds its token_budget, a slot's protected items alone exceed the slot's max_tokens, or the payload rendered from the protected items alone does not fit; nothing is omitted first. An item whose rendered body exceeds its token_budget MUST be reduced whether or not the payload fits: a compressible item to a supplied variant within the cap, and otherwise it is omitted; a droppable item is omitted; a protected item over its cap is never truncated. The route MAY cap a slot with max_tokens: the rendered bodies of the slot's included items, every occurrence counted, MUST then total at most max_tokens whether or not the payload fits. After token_budget caps and before budget pressure, the assembler MUST reduce the slot's own items in the same tier order until the slot is within its cap. The route MAY set a slot's min_tokens: during budget pressure the assembler MUST NOT make a reduction that leaves the slot's included tokens below it, and MUST NOT reduce that slot again once such a reduction is withheld; tier order still holds within the slot. Each omission for budget MUST be recorded in excluded with reason over_budget and stage assembler. The slot defaults set the minimum protection: in a slot that is protected by default, item metadata MUST NOT lower an item below protected, and an item that sets a lower tier there MUST be excluded with protected_tier_changed. In a slot that only the route raised to protected, an item MAY still lower its own tier. Only the route's versioned policy MAY raise a slot's tier. An item MUST NOT claim a tier above its slot's effective tier, and such an item MUST be excluded with reason tier_upgrade_not_allowed. Repeated occurrences count and are traced separately.

### R-17: Refused assembly has no rendered payload

When required protected content cannot fit, the assembler MUST refuse with protected_content_over_budget (R-16) rather than silently truncate. When the payload cannot fit without a reduction a slot's min_tokens withholds, the assembler MUST refuse with slot_floor_over_budget. A refused result MUST have no payload; its trace MUST set refused.bool: true, a non-empty reason, result: null, included: [] and compressed: [], and MUST keep every exclusion, conflict record and filled default recorded before the refusal. A successful trace MUST set refused.bool: false and refused.reason: null. A snapshot that fails its published schemas or the snapshot checks listed in conformance/README.md, or holds a string that is not well-formed Unicode or a number outside the IEEE 754 double range (I-JSON, RFC 7493), MUST be rejected before assembly, with no payload and no trace, because its profile, budget or context may be missing or contradictory. Rejection reports the application's error in building the snapshot; refusals are outcomes of valid snapshots.

### R-18: Precomputed variants; no model calls during assembly

Producers MUST compute rerank scores and any compression variants before assembly and SHOULD cache them by content hash. Each variant MUST have its own id, body, method and lineage, inherit its parent provenance, scope and authority, and MUST NOT introduce a new instruction or unsupported fact; an item whose variants repeat an id or reuse the item's own id MUST be excluded with duplicate_variant_id. Assembly MUST select only supplied variants and MUST NOT call a model. For each rendered occurrence of a variant, the trace MUST identify the parent item and the selected variant.

### R-24: Route-requested exact deduplication

When a route sets dedupe: exact on a slot, the assembler MUST, after conflict resolution and any supersession (R-25) and before any refusal check or fitting, exclude each item in that slot whose body equals the body of an item it keeps in the slot, with reason duplicate_content, stage assembler and duplicate_of naming the kept item. Bodies MUST be compared code unit for code unit after collapsing each run of whitespace to one space and trimming both ends, without Unicode normalization or case folding. The assembler MUST NOT exclude a protected item or an item a conflict group names: a set of equal bodies that contains one keeps every such item, and otherwise keeps its highest-ranked item by the slot's fitting rank. Deduplication never compares items across slots, and a slot without dedupe keeps equal bodies.

### R-25: Route-requested supersession of stale observations

When a route sets supersede: source on a slot, the assembler MUST, after conflict resolution and before deduplication, exclude each item in that slot that is neither protected nor named by a conflict group and for which another item in the slot, from the same authenticated producer and with the same source, has a later freshness, compared as instants at full precision. It MUST record each such exclusion with reason superseded, stage assembler and superseded_by naming the highest-ranked of the latest items by the slot's fitting rank. Items tied for the latest freshness are all kept. source and freshness decide alone: bodies, variants and source_version are not compared, and a slot without supersede keeps every observation.

### R-26: Route-requested source diversity

When a route sets max_per_source on a slot, the assembler MUST, after deduplication and before any refusal check or fitting, cap each pair of authenticated producer and source in the slot at that many items. Protected items and items a conflict group names are never excluded and take places first, even beyond the cap; the other items fill any places left in the slot's fitting rank, and the rest MUST be excluded with reason source_diversity_cap and stage assembler. Each slot is capped on its own, and a slot without max_per_source is not capped.

<!-- /generated:rulesFit -->

## 5 Placement profiles

Placement is model-, task- and content-dependent. This specification takes no position on where items go. It fixes the semantic slots and requires that placement be a **profile**: versioned, per route, and evaluated against that route's tasks before it's promoted for deployment (R-19). The evidence for this position is collected on the [Evidence](https://contextwindowarchitecture.io/evidence.html) page. Placement also decides how much of one call's payload the next call repeats byte for byte, which is what provider prompt caches reuse; the Evidence page's [section on prompt caches](https://contextwindowarchitecture.io/evidence.html#caching) sets out what the profile, the renderer and the application each own.

profile.yaml · an unevaluated draft · JSON syntax is valid YAML

<!-- generated:profile -->

```json
{
  "spec": "cwa/draft",
  "id": "policy-first-chat",
  "version": 1,
  "route": "support-chat",
  "model_family": null,
  "route_policy_version": "illustrative/v1",
  "placement": [
    {
      "slot": "governance.instructions",
      "wrap": "system"
    },
    {
      "slot": "state.user",
      "wrap": "xml:user_profile"
    },
    {
      "slot": "evidence.knowledge",
      "wrap": "xml:evidence"
    },
    {
      "slot": "state.task",
      "wrap": "xml:task"
    },
    {
      "slot": "interaction.memory",
      "wrap": "xml:memory"
    },
    {
      "slot": "interaction.history",
      "wrap": "xml:history"
    },
    {
      "slot": "governance.capabilities",
      "wrap": "tools"
    },
    {
      "slot": "evidence.tool_results",
      "wrap": "xml:observation"
    },
    {
      "slot": "governance.examples",
      "wrap": "xml:examples"
    },
    {
      "slot": "governance.output_contract",
      "wrap": "xml:format"
    },
    {
      "slot": "interaction.query",
      "wrap": "xml:query"
    }
  ],
  "evaluation": {
    "status": "unevaluated",
    "suite": null,
    "date": null,
    "result": null,
    "artifact": null
  }
}
```

<!-- /generated:profile -->

<!-- generated:rulesProf -->

### R-19: Draft profiles versus evaluated profiles

A profile MUST carry spec, id, version, route, model_family, ordered placement with wrapper rules, route_policy_version and an evaluation object. spec names the specification the profile was written for, cwa/draft until the first release; a profile for another specification MUST be rejected. Draft profiles MAY use model_family: null and evaluation.status: unevaluated. Promotion for a deployment MUST require a concrete model family/version and evaluation.status: evaluated with a suite/version, date, result and reproducible artifact location. Descriptive benchmark numbers without artifacts MUST NOT count as validation.

### R-20: Profile version and mandatory-slot validation

Every trace MUST record profile id and version. Any change to placement, repetition, wrapper rules, model target or referenced route policy MUST increment the profile version. A profile MUST include instructions and query, MUST include output_contract for parser routes, and MUST NOT omit any admitted protected content: when an admitted protected item's slot has no placement, the assembler MUST refuse with protected_slot_unplaced, and it MUST exclude an unprotected item in an unplaced slot with slot_unplaced. A profile's route and route_policy_version MUST equal the snapshot's route policy's route and version, and the snapshot's renderer MUST be able to realize its placements. Evaluation status changes alone MAY retain the version when the evaluated payload configuration is identical.

<!-- /generated:rulesProf -->

## 6 Trace & conformance tests

Every assembly emits a trace. "Debuggable" means an engineer can reconstruct and compare assembly decisions, not just read the payload. Outcome metrics ride on top: groundedness, task success, tool-call correctness, recovery behaviour, latency, cost.

**Trace fields**

MUST · trace_id · profile { id, version } · budget { input, reserved_output, margin_percent when the snapshot sets it } · context { spec, assembly_time, route_policy_version, tokenizer, renderer, snapshot_digest } · result { input_tokens, hash } or null · included[] { slot, item_id, tokens, source_version, eligibility } · compressed[] { slot, item_id, from, to, method, variant_id } · excluded[] { item_id, reason, stage }, plus slot when the candidate names one, and duplicate_of or superseded_by when the reason is duplicate_content or superseded · conflicts[] { group_id, kind, items, resolution, decided_by }, one per declared group, plus winner when one member prevails · refused { bool, reason } · recovery.action on an evidence_required refusal (R-12), or on a conflict_unresolved one when every unresolved group asked for context · defaults_filled[] { item_id, field }, empty when none were filled · reasons from contract/reasons.json

SHOULD · admission-stage timings

### 6.1 Tests the trace makes possible

<!-- generated:tests -->

| Test | What it shows | Requirement |
| --- | --- | --- |
| Assembly snapshot | Identical immutable assembly snapshots produce identical rendered bytes and hashes. | R-23 |
| Golden task | The right evidence item appears in the final context for a known request. | R-21 |
| Counterfactual ablation | Remove evidence, task state or tool results and confirm what fails, and that the trace explains it. | R-21 |
| Conflict | A malicious retrieved chunk with imperative text does not alter governing instructions. | R-7 |
| Budget pressure | At half the window, protected slots survive intact and shedding follows tier order: droppable first, then compressible. | R-16 |
| Freshness | Memory expired at assembly_time is excluded and the producer's exclusion reaches the trace. | R-9 |
| Refusal | When the evidence a route needs doesn't survive fitting, the assembler refuses with evidence_required instead of answering without it. | R-12 |
| Capability source | A tool specification emitted directly by an MCP adapter into governance.capabilities is excluded: as producer_slot_not_allowed, or as capability_not_allowed where the route lists that slot for the adapter. | R-15 |
| Cache reuse | Two consecutive turns of a frozen conversation under a cache-ordered profile render the same leading bytes through the last turn the earlier call held, so a breakpoint placed there on one call is still valid on the next. | R-7 |

<!-- /generated:tests -->

<!-- generated:rulesTrace -->

### R-21: Trace JSON matches the published schema

A conformant assembler MUST emit trace JSON satisfying schema/trace.schema.json: trace_id; profile {id, version}; budget {input, reserved_output, and margin_percent when the snapshot sets it}; context {spec, assembly_time, route_policy_version, tokenizer, renderer, snapshot_digest}, where context.spec equals the profile's spec; result {input_tokens, hash} or null on refusal; included[] {slot, item_id, tokens, source_version, eligibility}; compressed[] {slot, item_id, from, to, method, variant_id}; excluded[] {item_id, reason, stage}, plus duplicate_of or superseded_by when the reason is duplicate_content or superseded; conflicts[] {group_id, kind, items, resolution, decided_by}; refused {bool, reason}; defaults_filled[] {item_id, field}; and recovery.action when a refusal records one (R-11, R-12). included records represent rendered occurrences. result.input_tokens includes rendering overhead; hash is lowercase SHA-256 of the exact rendered UTF-8 payload. Exclusion and refusal reasons MUST use the codes published in contract/reasons.json for the conditions those codes name. When an item fails several checks, the recorded reason MUST be the earliest applicable exclusion code in that file's order; among several missing_field codes, the alphabetically first field name is recorded. When several refusal conditions hold, the recorded reason MUST be the earliest refusal code in that file's order. Where these requirements leave an ordering, tie-break, boundary or algorithm step open, conformance/README.md is normative. Schema validation alone MUST NOT be described as implementation conformance.

### R-22: Provenance, snapshot digest and filled defaults in the trace

A trace MUST include source_version and eligibility for each included occurrence, the slot of each assembler-stage excluded item whose candidate names one of the eleven slots, and context.snapshot_digest as a lowercase SHA-256 identifying the frozen assembly snapshot. defaults_filled MUST list one {item_id, field} record per item and field filled under R-3, and MUST be an empty list when no defaults were applied. A trace SHOULD include non-negative admission-stage timings.

### R-23: Determinism includes the clock and policy snapshot

Given identical items, variants, producer exclusions, conflict groups, authenticated producer context, capability allow-list, scope, route-policy version and configuration, profile, tokenizer, renderer, assembly_time and budget, an assembler MUST produce identical rendered UTF-8 payload bytes and the same SHA-256 result hash, or the same refusal decision. Any mutable external reads or model calls MUST occur before that immutable assembly snapshot. Trace IDs and measured timing fields MAY differ; they are not part of the payload hash.

<!-- /generated:rulesTrace -->

## Future work · non-normative

A future revision will describe request intent as a typed tree that items bind to, so that eligibility rules can reference the part of the request an item serves rather than the request as a whole. Machine-readable schemas and contract fixtures are available in this repository.

Two extensions wait until a producer needs them. A **producer call key** would let supersession (R-25) group observations by the call they answer rather than by source, so that source could name the server or tool a citation points to; supersede is an enum, so a call-key mode can join source without a new field. A **cluster mode** for deduplication (R-24) would collapse chunks that share a retriever-computed cluster id; until a clustering service spans producers, a retriever drops its own near-duplicates and reports each one (R-13), which keeps every exclusion in the trace. Four assemblers, in Python, TypeScript, Go and Rust, implement the complete specification and pass every published conformance case, and none is released; their conformance status is tracked on the [Assembler](https://contextwindowarchitecture.io/assembler.html) page.

The eligibility predicate is closed at the slot-level rules R-3 lists. A future specification version may introduce additional eligibility rules or an extension mechanism with defined snapshot, evaluation, and conformance requirements.
