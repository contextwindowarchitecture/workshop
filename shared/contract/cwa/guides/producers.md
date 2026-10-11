# CWA for producers

> How to build a producer for Context Window Architecture (CWA): anything that emits candidate items into a slot, such as a retriever, a memory store, an MCP adapter, a state service, the capability policy, a policy loader or the conversation. It follows the Producers page, https://contextwindowarchitecture.io/producers.html. Rules are cited by their permanent number (R-n) and are normative in [SPEC.md](../SPEC.md), which the Spec page, https://contextwindowarchitecture.io/spec.html, renders. Its list of stages, its tables of slots, authority values and exclusion codes, and its example batch are written from the contract files by `python3 conformance/check.py --write`.

## What a producer is

The assembler does not know how a producer works. It knows only what the producer hands over, and that handover is the contract. The application authenticates each producer and the route policy lists it under that identity, with one of seven kinds and the slots it may send: `retrieval`, `memory`, `mcp`, `state`, `capability_policy`, `policy` or `interaction` (R-15). Nothing in an item's own fields proves who sent it, neither `source` nor `trust`.

A conformant producer (spec §1) emits only items that meet section 2's rules for an item (R-1, R-2), which admission checks, plus the MUSTs aimed at producers:

- every producer reports each entry it suppresses (R-9) and computes its scores and variants before assembly (R-18);
- by kind, R-9 and R-14 bind memory, R-10 anything carrying user-controlled or fetched content, R-13 retrievers, R-15 MCP adapters, and R-18's variant rules anything that supplies variants.

The claim rests on the producer's word. Admission catches some breaches and excludes the item with a reason code the trace records; others, such as a retriever that merged chunks or dropped one without reporting it, no assembler can see.

## Who owns which stage

Between a source and the payload there are eight steps (spec §4). The first four are the producer's and happen before assembly starts. The last four are the assembler's, and everything it leaves out shows up in the trace with a reason code.

<!-- generated:stages -->

1. Rewrite (producer): Decide whether to rewrite the query for retrieval, and keep the rewritten form so you can explain the results later.
2. Retrieve (producer): Pull candidate chunks from sources whose provenance you can name.
3. Rerank (producer): Score each candidate against the query and put the score in relevance. If you drop a near-duplicate, report it as duplicate_content, with duplicate_of naming the one you kept (R-13).
4. Package (producer): Send each chunk as its own evidence item with source, source_version, relevance and the authority its evidence slot takes (R-1). Never one merged blob (R-13).
5. Admit (assembler): Check each item against its schema and the route: who sent it, which slot, what authority, its scope, age and expiry, and the route's min_relevance. Anything that fails is excluded with a reason code.
6. Resolve (assembler): Settle the conflict groups the application declared (R-11). Then, in the slots where the route asks, drop superseded observations (R-25), exact duplicates (R-24) and anything past max_per_source (R-26), in that order.
7. Fit (assembler): Refuse before any reduction if protected content can't fit (R-16, R-17). Otherwise apply item and slot caps, then shed in tier order under budget pressure: droppable first, then compressible (R-16). If too little evidence is left on a route that requires it, refuse instead (R-12).
8. Render & trace (assembler): Render the payload in the profile's order, hash it, and write a trace that accounts for every decision above (R-21).

<!-- /generated:stages -->

## The batch

Whatever its kind, a producer hands over one batch per call: `{ items, excluded }`, as schema/producer_batch.schema.json defines it. When the application freezes the snapshot it adds `producer: { id, kind }`, the identity it authenticated for the batch, never read from item fields (R-15).

- `items` are your candidate items, each admitted or excluded on its own. An entry that is not a JSON object is not an item: the snapshot holding it is rejected (R-2, R-17).
- `excluded` has one row per entry you suppressed: `{ item_id, reason, stage: "producer" }`, with `reason` one of the exclusion codes below (R-9). A `duplicate_content` row carries `duplicate_of` and a `superseded` row `superseded_by`, no other row carries either, and each names a candidate in the same batch (R-9, R-13).
- Ids are unique across `items` and `excluded`, and across the snapshot: a candidate whose id another candidate or a producer exclusion uses, in any batch, is excluded with `duplicate_item_id` (R-2).
- A snapshot holds at most one batch per producer (R-15). A second batch from the same producer, an excluded row whose `duplicate_of` or `superseded_by` names no candidate in its batch, or a `reason` that is not an exclusion code rejects the whole snapshot before assembly, with no payload and no trace (R-17).
- Your rows reach the trace as reported, at `stage: "producer"` and with no slot, ahead of the assembler's rows, even from a batch whose producer the route does not admit (R-9). Every other row is the assembler's own, at `stage: "assembler"`.

The published example batch, examples/producer-batch.json:

<!-- generated:batch -->

```json
{
  "items": [
    {
      "id": "refunds-eu:v17#p4",
      "slot": "evidence.knowledge",
      "source": "policy-corpus",
      "source_version": "2026-09-10",
      "authority": "reference_only",
      "trust": "verified",
      "freshness": "2026-09-12T15:30:00Z",
      "expires": "2026-12-12T15:30:00Z",
      "scope": {
        "tenant": "acme",
        "task": "refund_request"
      },
      "relevance": 0.91,
      "token_budget": 420,
      "tier": "compressible",
      "variants": [],
      "conflict_policy": "defers",
      "injection_risk": "untrusted_content",
      "lineage": "verbatim",
      "eligibility": "support-chat/illustrative/v1: tenant acme; rerank at least 0.5",
      "body": "Pro plans refund in full within 30 days of purchase."
    }
  ],
  "excluded": [
    {
      "item_id": "memory:expired",
      "reason": "expired",
      "stage": "producer"
    }
  ]
}
```

<!-- /generated:batch -->

## The item

Every item carries eight fields: `id`, `slot`, `source`, `source_version`, `authority`, `freshness`, `trust` and `body`. Without them the assembler cannot place, rank, expire or trace the item, so it excludes it with `missing_field:<name>` (R-2). Two slots need one more, whoever produces the item: every `interaction.memory` item carries `expires` (R-9), and every `evidence.knowledge` item its rerank score in `relevance` (R-13). The item schema is closed, so an undeclared field, a wrong type or a malformed timestamp is `invalid_structure`.

| Field | Required | What it holds |
| --- | --- | --- |
| `id` | always | A string with at least one character that is not whitespace, unique in the snapshot. An item without one is recorded as `{producer id}#invalid-{n}` (R-2). |
| `slot` | always | One of the eleven slots in the table below; any other value is `unknown_slot` (R-1). |
| `source` | always | What the item came from: a document, turn, tool call, database field or memory write. A retriever sets it to the document a chunk comes from, so chunks of one document share it (R-26); repeated reads of the same thing share one, so supersession can keep the latest (R-25); a memory item names the turn it came from (R-9). |
| `source_version` | always | The version of that source. The trace repeats it for every included occurrence (R-22). |
| `authority` | always | One of seven values, fixed by the slot (R-1); see the tables below. |
| `freshness` | always | When the content was observed or true, an RFC 3339 date-time. It is not an expiry. |
| `trust` | always | `verified`, `unverified` or `untrusted`: the producer's own claim about its source, so it proves nothing (R-15). Only the governance gate reads it: a governance item must be `verified` (R-10). It never decides who may instruct or which fact wins. |
| `body` | always | The content. Assembly renders a body whole and never splits, edits or truncates it. |
| `expires` | memory | An absolute deadline, not a duration. Any item, memory or not, whose `expires` is at or before `assembly_time` is excluded as `expired` (R-9). |
| `relevance` | knowledge | The rerank score, a finite number, read as an IEEE 754 double like every number in a snapshot (R-2). A score equal to the slot's `min_relevance` passes (R-13). |
| `scope` | no | Any of `tenant`, `user`, `session`, `task`, `locale` and `step`. Every key you set must equal the request's value for it, and a slot's `required_scope` lists keys you must set; a missing key is never a wildcard (R-2). |
| `tier` | no | `protected`, `compressible` or `droppable`. Leave it out to take the slot's tier. You may lower it, except in a slot protected by default, and never raise it (R-16). |
| `revoked_by` | no | Set when the application revoked the item. Any item carrying it is excluded as `revoked` (R-9). |

Six policy fields describe how an item may be handled. A producer that knows better than the slot default SHOULD set them; when it does not, the assembler fills them from the slot defaults, or from the route's versioned overrides, and the trace lists every field it filled in `defaults_filled` (R-3).

- `token_budget` caps the tokens of the item's rendered body. `null`, the default, sets no cap of its own; the payload budget and the slot's `max_tokens` still bound the item. An item over its cap is reduced whether or not the payload fits: a compressible item to a variant within the cap, or else it is omitted, and a droppable item is omitted. A protected item over its cap is never cut: the assembly refuses with `protected_content_over_budget` (R-16).
- `variants` holds shorter bodies you computed ahead of time (see Variants and scores below). It defaults to an empty list.
- `conflict_policy` is `defers`, `governs` or `escalate`. It matters only inside a conflict group the application declares, and only between the peers that may instruct: the members at the highest instructing authority present. When exactly one peer governs and the rest defer, the deferring ones are excluded with `conflict_deferred`; any other pattern escalates (R-11). Facts ignore it; route policy decides them.
- `lineage` is `verbatim`, `summarised`, `redacted`, `translated`, `extracted` or `generated`.
- `eligibility` is a short description of why the item belongs in the request, for whoever reads the trace. It is never code and never blank, and the trace repeats it for every included occurrence (R-3, R-22). The route's slot rules decide what is eligible: `min_relevance`, `max_age_seconds`, `required_scope` and `source_prefix`, and no others (R-3).
- `injection_risk` is `none` or `untrusted_content` (see Untrusted content below).

Every date-time is `YYYY-MM-DDTHH:MM:SS`, an optional fraction of any length, then `Z` or an offset `±HH:MM`. The date must exist, there are no leap seconds, and assemblers compare instants at their full stated precision (R-2). An item whose `freshness` is later than `assembly_time` by more than the route's `clock_skew_seconds` (default 0) is excluded with `future_freshness`.

## Slots, authority and defaults

Each slot takes the authority shown, and the defaults fill the policy fields an item omits (R-1, R-3; contract/slot-defaults.json):

<!-- generated:slots -->

| Slot | Plane | Holds | Authority | Tier | Lineage | injection_risk | conflict_policy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `governance.instructions` | Governance | Identity, goals, refusals, and safety boundaries: the system's constitution. | `governing` | protected | verbatim | none | governs |
| `governance.capabilities` | Governance | The tools, functions and resources the model is permitted to invoke, with their contracts. | `governing` | protected | verbatim | none | governs |
| `governance.examples` | Governance | Developer-owned input/output pairs that steer reasoning, tone or format, ranked by task similarity. | `governing` | droppable | verbatim | none | defers |
| `governance.output_contract` | Governance | Structure, style, length and schema of the response about to be generated. | `governing` | protected | verbatim | none | governs |
| `state.user` | State | Durable profile, entitlements, locale, permissions, session preferences, each a separate item with its own freshness. | `state` | droppable | extracted | none | governs |
| `state.task` | State | Workflow stage, approval status, selected entity IDs, pending action, retry count. | `state` | protected | extracted | none | governs |
| `evidence.knowledge` | Evidence | Retrieved chunks, each sent as its own evidence item with source, version, relevance and trust. | `reference_only` | compressible | verbatim | untrusted_content | defers |
| `evidence.tool_results` | Evidence | Observations returned by tools already called, possibly several per loop, and any retrieved chunks a route sends here. | `observation` | compressible | verbatim | untrusted_content | governs |
| `interaction.memory` | Interaction | Condensed summaries of older turns and inferred long-term facts, each linked to the turn it came from. | `generated` | compressible | summarised | untrusted_content | defers |
| `interaction.history` | Interaction | A verbatim transcript of the most recent turns, bounded by turn count and tokens. | `user` | compressible | verbatim | untrusted_content | defers |
| `interaction.query` | Interaction | The most recent, unprocessed input the model must respond to. | `user` | protected | verbatim | untrusted_content | defers |

<!-- /generated:slots -->

The authority column has two exceptions: a prior model turn in `interaction.history`, marked `lineage: generated`, carries `untrusted`, and any other item in `evidence.tool_results`, `interaction.memory` or `interaction.history` may carry `untrusted` instead (R-1). An authority outside the seven is `unknown_authority`, and one the slot does not take is `authority_not_allowed`. Only `governing` and `user` items may instruct the model; the other five values record where data came from and are not a ranking of which facts are true (R-6).

<!-- generated:authority -->

| Authority | Role | Meaning |
| --- | --- | --- |
| `governing` | Governing instruction | System and developer policy, safety constraints, the output contract, admitted capabilities, and steering examples. |
| `user` | User intent / preference | What the user asks for and how they want it. It cannot lift a constraint set above it. |
| `state` | Canonical state | Application-owned facts about the task and session. The route defines the facts for which this source is canonical. |
| `reference_only` | Reference evidence | Retrieved chunks in knowledge, which inform the answer but never direct behaviour. |
| `observation` | Tool observation | What a tool returned, and any retrieved chunk a route sends to tool results: evidence about the world, not permission to act on it. |
| `generated` | Generated memory | Summaries and inferences the system wrote. They are fallible, they expire, and they can be revoked. |
| `untrusted` | Untrusted (least privilege) | Prior model turns in history, which must carry it, and any other item in tool results, memory or history whose producer wants it handled with the least privilege. It keeps the item out of an instruction group's peers and changes nothing else. Governance, knowledge, state and the query never carry it. Not the same as injection_risk: untrusted_content, which flags content that might carry an injection. |

<!-- /generated:authority -->

The tier column is the highest tier your items can claim. Only the route's versioned policy can raise a slot's tier, and an item that claims more than its slot's tier is excluded with `tier_upgrade_not_allowed`, so a producer cannot protect its own items. In a slot that is protected by default the tier is also the lowest: an item that sets a lower one there is excluded with `protected_tier_changed`. Anywhere else you may lower an item's tier, say to `droppable` so it sheds earlier, even in a slot only the route raised to protected (R-16).

## Producer kinds

A producer's kind limits the slots it may send, whatever the route lists, and an item in a slot the route does not list for its producer is excluded with `producer_slot_not_allowed` (R-15). An item from a producer the route does not list, or lists with another kind, is excluded with `producer_not_authenticated`.

### Retrieval: evidence.knowledge and evidence.tool_results

One scored item per chunk, never a blob (R-13). Emit one evidence item per chunk, with `authority: reference_only` in knowledge or `observation` in tool results, its rerank score in `relevance` and its `source_version`, and set `source` to the document the chunk comes from, so chunks from one document share it. The retriever owns rewrite, retrieve, rerank and package, and any near-duplicate filtering: report each chunk it drops as a near-duplicate in `excluded` with reason `duplicate_content` and `duplicate_of` naming the chunk it kept, a candidate in the same batch. Every `evidence.knowledge` item, from any producer, carries `relevance`, or it is excluded with `missing_field:relevance`. An item a retriever sends to any slot but the two evidence slots is excluded with `producer_slot_not_allowed`, whatever the route lists.

An empty result set is a valid, recorded outcome, so do not pad it: on a route that requires evidence, the assembler refuses with `evidence_required` and a recovery action, and any retry is a new snapshot (R-12). Nor over-fill it: send no more chunks than the route's budget can use, since every chunk the assembler sheds for budget costs a count of the whole payload.

### Memory: interaction.memory

The state-versus-memory distinction, expressed as fields (R-9, R-14). Emit only `generated` or `untrusted` items. Every entry carries `expires`, an absolute deadline, not a duration. Its `source` identifies the turn it was derived from; a route may set the slot's `source_prefix`, such as `turn:`, and an entry whose source lacks it is excluded with `source_invalid` (R-3). Omit `lineage` and the slot default, `summarised`, is filled in.

The producer does not decide what the user has contradicted: the application revokes the entry, and the store records `revoked_by`. Never emit an expired or revoked entry as a candidate. Report each in the batch's `excluded` list with reason `expired` or `revoked` and `stage: "producer"`, without its body, and the assembler merges those rows into its trace. An item sent to any slot but `interaction.memory` is excluded with `producer_slot_not_allowed`, whatever the route lists.

### State: state.user and state.task

Owned by the application, and either current or absent (R-8). A state producer reads the database or the workflow engine and emits one item per fact, typed, with `authority: state` and `freshness` set to the read time. It never derives a value from conversation, and claims the user made about themselves go to memory, not state. The route lists it with `kind: state`: a state item from any other kind of producer is excluded with `producer_slot_not_allowed`, whatever slots the route lists for it, and an item older than the slot's `max_age_seconds` is excluded as `stale_state`.

`state.task` is protected by default: it is never shed, an item that sets a lower tier there is excluded with `protected_tier_changed`, and a `state.task` item over its own `token_budget`, or `state.task` items over the slot's `max_tokens`, refuse the whole assembly with `protected_content_over_budget`. `state.user` is droppable by default, so it sheds first under budget pressure, and an item that claims a higher tier is excluded with `tier_upgrade_not_allowed` (R-16).

### MCP: evidence.tool_results and evidence.knowledge

Results go to evidence; tool specifications are proposed, never placed (R-15). Tool results and resources become `evidence.tool_results` items with `authority: observation`, or `evidence.knowledge` items with `reference_only`, each with a `freshness` and `injection_risk: untrusted_content` unless the route lists the server with `verified: true`. That flag is the route's to grant, never the adapter's (R-10), and it does nothing else: it never ranks the server's claims in a fact group (R-11). A resource bound for knowledge needs a `relevance` score like any retrieved chunk. Where the route sets `supersede: source` on tool results, only the newest observation per source survives (R-25), so give repeated reads of the same thing the same `source`. A resource that contains imperatives is still evidence.

Tool specifications are proposed to the route's capability policy; the adapter never writes to `governance.capabilities` itself. An item it emits there is excluded with `capability_not_allowed` where the route lists that slot for the adapter, and with `producer_slot_not_allowed` otherwise, as is anything it sends to a slot other than the two evidence slots, whatever the route lists.

### Capability policy: governance.capabilities

Owned by the application, and the only producer for this slot (R-15, R-5). The capability policy holds the versioned allow-list of tools per route and user. It takes proposed specifications from MCP adapters and local tool registries, admits the ones this user may use, and emits one item per tool with `authority: governing`, `trust: verified` and `injection_risk: none`. The allow-list makes a natural `source`, and its version with the specification's content hash a natural `source_version`.

The route lists the policy with `kind: capability_policy`, and the snapshot carries its grant, `capabilities: { policy_producer, allow_list_version, allowed_ids }`. A `governance.capabilities` item is admitted only when its batch comes from the grant's `policy_producer`, the route lists that producer with kind `capability_policy`, and `allowed_ids` names the item's id; any other is excluded with `capability_not_allowed`. Permission is decided here, outside the model: the model is told what it may call, and the tool guard still enforces it.

### Policy and interaction: whatever the route lists

These two kinds have no slot rule of their own. They may send whatever slots the route lists for them, except the state slots, which take only kind `state` (R-8), and `governance.capabilities`, which takes only the capability policy's grant (R-15). In the published route policies, a `policy` producer sends the governance slots and an `interaction` producer, the conversation, sends `interaction.history` and `interaction.query`.

- Governance items carry `authority: governing`, `trust: verified` and `injection_risk: none`. One that is not verified, or is marked `untrusted_content`, is excluded with `untrusted_in_governance` (R-10).
- The query carries `user` authority, keeps it although it is marked `untrusted_content`, and is the only live user turn (R-1, R-7, R-10).
- Prior turns go to `interaction.history` and render as a transcript inside the profile's history wrapper, never as platform messages (R-7). A user turn carries `user`; a prior model turn carries `lineage: generated` and `authority: untrusted` (R-1).
- Turns render in the order they were said: by `freshness`, then `id` (R-7). Give each turn the instant it was said, not the time you read it from the conversation store; turns stamped alike fall back to id order.
- Compact old turns in blocks, one summary standing for many turns and unchanged until the next compaction, rather than dropping one turn per call, so the history's leading part repeats from call to call and a provider's prompt cache can reuse it.
- A route that sets `supersede: source` or `dedupe: exact` on `interaction.history` drops turns: supersession keeps only the latest turn per source (R-25), and deduplication drops a reply that repeats an earlier one (R-24). Give each turn a source of its own, and leave deduplication off there unless dropping repeats is intended.

## Untrusted content

Every item in an evidence slot, in memory, in history and in the query carries `injection_risk: untrusted_content`, whoever produced it: retrieved chunks, tool output, memory and user turns alike (R-10). The slot default fills it when you omit it, and an item that sets `none` there is excluded with `untrusted_content_unmarked`. The one exception is output from an MCP server the route lists with `verified: true`, which only the authenticated route policy can grant (R-15).

The marker never changes authority or where an item renders (R-6, R-10). Material a user pastes or attaches into the body of a query or history item renders with that body, since assembly never splits one, and gains no authority from it; delimit such material inside the body in a form it cannot imitate. Material you receive separately belongs in an item of its own, marked.

## Variants and scores

Compression variants and rerank scores are the producer's job, computed before assembly, and they should be cached by content hash. Assembly never calls a model (R-18). If your producer can offer a shorter form of an item, emit it as a variant on the item, not as a second item. Each variant is `{ id, body, method, lineage }`, with an id distinct from its parent's and its siblings' (or the item is excluded with `duplicate_variant_id`). It inherits the parent's provenance, scope and authority, and must not add an instruction or a fact the parent does not support.

The assembler picks a variant only when its rendered body is shorter than the item's current one. An item over its `token_budget` takes its longest variant within the cap, and a compressible item with none is omitted (R-16). Under budget pressure, droppable items go first, except those a slot held at its `min_tokens` floor keeps, and then compressible items are compressed or omitted in the route's fitting order, variants first when the route declares none. Protected items are never compressed, truncated or omitted. Every omission is traced as `over_budget`.

## Admission failures

Every exclusion lands in the trace as `excluded[] { item_id, reason, stage }`, plus `duplicate_of` or `superseded_by` when the reason calls for it. When an item fails several checks, the assembler records the earliest code in this list, and among several missing fields the alphabetically first (R-21). These are the codes a producer can meet, in that order (contract/reasons.json):

<!-- generated:exclusions -->

| Code | Rule | When |
| --- | --- | --- |
| `producer_not_authenticated` | R-15 | The route policy does not list this batch's producer, or lists it with a different kind. Identity comes from the application's authentication and the route, never from item fields. A snapshot with two batches from one producer is rejected before assembly. |
| `missing_field:<name>` | R-2 | A required field of the item itself is absent: one of the eight minimum fields, or a slot-specific one such as expires for memory or relevance for knowledge. A variant missing one of its fields is invalid_structure. Fix the producer; the assembler will not guess. |
| `unknown_slot` | R-1 | The slot is not one of the eleven slot names, whatever its JSON type: a number, null, an array or an object is unknown_slot too, not invalid_structure, since this code comes first (R-21). Check spelling and plane prefix. |
| `unknown_authority` | R-1 | The authority is not one of the seven roles, whatever its JSON type: a number, null, an array or an object is unknown_authority too, not invalid_structure, since this code comes first (R-21). capability and steering are not authority values; use governing with a conflict_policy. |
| `invalid_structure` | R-2 | The item fails the published schema for another reason, such as a wrong type, an undeclared field or a malformed timestamp. |
| `duplicate_item_id` | R-2 | Another candidate, in any batch and whatever its own outcome, or a producer exclusion from any batch uses this ID. Each candidate sharing it is excluded with the earliest code that applies to it. |
| `producer_slot_not_allowed` | R-15 | The authenticated producer is not permitted to emit into this slot: the route does not list the slot for it, or its kind rules the slot out whatever the route lists. State slots take only kind state (R-8), a memory producer only interaction.memory (R-14), a retrieval producer only the evidence slots (R-13), and an mcp producer only the evidence slots, plus governance.capabilities when the route lists it for the producer, where capability_not_allowed applies (R-15). |
| `authority_not_allowed` | R-1 | The authority value is not allowed for this slot. Each slot takes its own role, a prior model turn in history takes untrusted, and only other items in tool results, memory and history may carry untrusted instead (R-1): never governance, knowledge, state or the query. These roles are not a factual ranking. |
| `capability_not_allowed` | R-15 | The snapshot carries no capability grant, the authenticated emitter is not the producer the grant names as policy_producer listed by the route with kind capability_policy, or the tool is not on the grant's allow-list. Item source strings cannot prove permission. |
| `untrusted_in_governance` | R-10 | A governance item is not verified or is marked untrusted_content. |
| `untrusted_content_unmarked` | R-10 | The item is in a slot whose published injection_risk default is untrusted_content (evidence.knowledge, evidence.tool_results, interaction.memory, interaction.history or interaction.query) but is not marked untrusted_content, and no MCP server the route verified produced it (R-10, R-15). |
| `protected_tier_changed` | R-16 | The item sets a tier below protected in a slot whose default tier is protected. In a slot only the route raised, an item may lower its own tier. |
| `tier_upgrade_not_allowed` | R-16 | The item claims a tier above its slot's effective tier. Only the route's versioned policy can raise a tier; a producer cannot protect its own items. |
| `duplicate_variant_id` | R-18 | Variant IDs repeat, or a variant reuses its parent item's ID. |
| `revoked` | R-9 | revoked_by is set. The item was contradicted or withdrawn. |
| `expired` | R-9 | expires is at or before assembly_time. freshness describes when content was true; a past freshness is not itself expiration. |
| `future_freshness` | R-2 | freshness is later than assembly_time by more than the route's clock_skew_seconds (default 0), compared at full precision. |
| `stale_state` | R-8 | A state item was observed longer ago than its slot's max_age_seconds. State must be current at assembly time. |
| `source_invalid` | R-3 | The item's source does not start with its slot's source_prefix. For memory, this is how the source turn is identified (R-9). |
| `out_of_scope` | R-2 | A scope key the item carries has a value other than the request's, or the request lacks that key, or the item lacks a key its slot's required_scope lists. A missing key is never a wildcard. |
| `below_threshold` | R-13 | The rerank score is under its slot's min_relevance, or the item has no score in a slot that sets one. A score equal to the threshold passes. An evidence.knowledge item always needs a score, so one without it is missing_field:relevance instead (R-13). |
| `not_eligible` | R-3 | The item was observed longer ago than its slot's max_age_seconds, in a slot other than a state slot, where the code is stale_state. The slot-level eligibility rules are the complete predicate (R-3); no other rule excludes an item this way. |
| `slot_unplaced` | R-20 | The profile has no placement for the item's slot, and the item is not protected. A protected item in an unplaced slot is never excluded; assembly refuses with protected_slot_unplaced. A profile that does not place instructions and query, or the output contract on a parser route, is rejected with its snapshot before assembly. |
| `conflict_deferred` | R-11 | The item is a peer instruction with conflict_policy defers, and the one peer in its declared conflict group that governs prevailed. A protected item is never excluded this way; its group escalates. |
| `conflict_lost` | R-11 | Route fact policy chose another member of the item's declared fact conflict group, by authenticated producer precedence or an allowed freshness tie-break. A protected item is never excluded this way; its group escalates. |
| `superseded` | R-25 | The route asked this slot to supersede by source, and the same producer sent a later observation with the same source. superseded_by names the item kept. |
| `duplicate_content` | R-24 | The item's body duplicates a kept item's: either the route asked this slot for exact deduplication and the bodies match once whitespace is collapsed (R-24), or a retriever dropped it as a near-duplicate and reported it at stage producer (R-13). duplicate_of names the item kept. |
| `source_diversity_cap` | R-26 | The route caps this slot at max_per_source items per producer and source, and higher-ranked or exempt items from the same source filled every place. |
| `over_budget` | R-16 | The item was omitted to fit the rendered budget, its own token_budget or its slot's max_tokens, in tier order and by the route's fitting policy. |

<!-- /generated:exclusions -->

## Checking your output

- Validate each item against schema/context_item.schema.json and each batch against schema/producer_batch.schema.json with a JSON Schema 2020-12 validator that asserts `format`. The date-time `pattern` pins the shape but not the calendar, so a validator that leaves `format: date-time` unasserted accepts `2026-02-30`.
- The Producers page shows the site's local checks at work on sample items and batches, to see CWA in action rather than to check your own output. `checkItem` and `checkProducerBatch` in https://contextwindowarchitecture.io/contract.js run the same checks. They judge structure and the rules an item shows on its own. They cannot authenticate producers or apply the route, so producer kinds and their slots, the capability grant, the verified flag, scope, `max_age_seconds`, `min_relevance`, `source_prefix`, placement and ids across a snapshot go unchecked. Passing them is not admission.
- Admission happens in an assembler. To see it, freeze a snapshot that holds your batch and run it through one of the implementations (the [assembler guide](assemblers.md)): the trace's `excluded` rows say what happened to each item, and `defaults_filled` which fields the assembler filled.

## Sources

- Producer contract page: https://contextwindowarchitecture.io/producers.html
- Spec, sections 2 to 4: https://contextwindowarchitecture.io/spec.html
- Requirements: [SPEC.md](../SPEC.md)
- Item schema: [schema/context_item.schema.json](../schema/context_item.schema.json)
- Producer-batch schema: [schema/producer_batch.schema.json](../schema/producer_batch.schema.json)
- Route-policy schema, where producers, slot rules and fact precedence live: [schema/route_policy.schema.json](../schema/route_policy.schema.json)
- Slot defaults: [contract/slot-defaults.json](../contract/slot-defaults.json)
- Reason codes: [contract/reasons.json](../contract/reasons.json)
- Example item: [examples/context-item.json](../examples/context-item.json)
- Example route policies: [examples/route-policies.json](../examples/route-policies.json)
- The whole contract in one file: https://contextwindowarchitecture.io/llms-full.txt
