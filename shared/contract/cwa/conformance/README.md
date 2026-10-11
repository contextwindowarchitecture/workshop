# CWA conformance cases

Language-neutral test cases for assemblers. Each directory under `cases/` holds:

| File | Contents |
| --- | --- |
| `case.json` | `id`, the requirement IDs the case exercises (`rules`), and a one-sentence `description` |
| `snapshot.json` | The frozen assembly input, valid against `schema/snapshot.schema.json` |
| `expected.trace.json` | The trace a conformant assembler emits, valid against `schema/trace.schema.json` |
| `expected.payload.txt` | The exact rendered payload bytes; absent when the case expects a refusal |

Each directory under `rejections/` holds a `case.json` and a `snapshot.json` that breaks exactly one of the Snapshot checks or its schemas. A conformant assembler rejects it before assembly, so there is no expected trace or payload (R-17).

One profile id and version name one profile across the corpus, as R-20 requires of any change, and one route and version name one route policy, as Registry requires: a case's profile takes the case's id or an id no other case uses, a rejection that changes its profile takes the rejection's, and a rejection that changes its route policy gives it a version of its own.

Some cases have a generator in `generators/`. It holds a table of each candidate's intended outcome, and it derives the expected trace and payload from that table rather than from any assembler's logic. Regenerate a case with `python3 conformance/generators/<case>.py`, or every generated case, then the rejections and the registry, which read some of them, with `python3 conformance/generators/all.py`, and review the diff.

`check.py` checks the contract's own consistency: every case and rejection against the schemas, digests and hashes against their definitions here, each rejection against exactly one Snapshot check, reason codes against the requirements that cite them, the examples and every published payload's rendering and count, `SPEC.md` and the guides against the contract files, and the implementations' stored reports. Run `python3 conformance/check.py` after editing any of them; `python3 conformance/check.py --write` rewrites the blocks of `SPEC.md` and the guides that are written from the contract files. `python3 -m unittest discover -s conformance/tests` holds the schemas to their rules one change at a time, checks the import tool, and regenerates every case to show nothing changes. `check.py` needs the `jsonschema` and `rfc3339-validator` packages, the second so that `format: date-time` is asserted (Timestamps), and it stops when it is not. `pyproject.toml` names both, so `uv run python conformance/check.py` runs it with nothing else installed.

## Running a case

1. Validate `snapshot.json` and load it. A snapshot that fails its schemas or any check in Snapshot checks is rejected before assembly and has no trace (R-17). Resolve `tokenizer` and `renderer` by ID. Every implementation provides the ones Tokenizers and renderers requires; a case that uses an optional one the implementation does not provide is skipped, not passed (Reporting results).
2. Assemble.
3. Compare the payload byte for byte with `expected.payload.txt`, or confirm no payload when that file is absent.
4. Compare the trace with `expected.trace.json` after removing `trace_id`, `timings` and `recovery.detail`, which may differ (R-23). `recovery.detail` is free text for people, and no requirement defines its content. `context.snapshot_digest` is compared like every other field; Snapshot digest defines it.

Array order in the trace is part of the expectation:

- `included[]` follows placement order and, within a placement, the renderer's item order: `id` order, except in `interaction.history`, whose turns go by `freshness` as instants at full precision (Timestamps) and then by `id` (R-7). For `fixture-xml/v1` that is payload order.
- `excluded[]` lists producer-stage rows first, ordered by producer id, then `item_id`, then the bytes of their RFC 8785 serialization. They come from every batch, including one whose producer the route does not admit: they carry no content, and R-9 merges them. Assembler rows follow in pipeline order. Admission rows are ordered by producer id, then recorded `item_id`, and candidates sharing an id by the bytes of their own RFC 8785 serialization, as Snapshot digest orders them, so snapshots with the same digest give the same trace. Conflict rows follow, ordered by `item_id`, then supersession, deduplication and source-diversity rows, each stage ordered by `item_id`, and fitting rows follow in the order items were omitted.
- `conflicts[]` has one record per declared group, ordered by `group_id`.
- `compressed[]` has one row per included occurrence of a compressed item, in `included[]` order.
- Assembler rows in `excluded[]` carry `slot` whenever the candidate names one of the eleven slots, even when it fails for another reason (R-22). Producer rows carry what the producer reported, which has no slot.
- `defaults_filled[]` is ordered by `item_id`, then by field in R-3 order: `token_budget`, `variants`, `conflict_policy`, `lineage`, `eligibility`, `injection_risk`. It covers every schema-valid item from a producer the route admits, including items later excluded, because later admission checks read the filled values. `admission-reasons` holds two items excluded with `duplicate_item_id` that leave `lineage` to the slot default, so each still has its row.

Each `included[]` row carries the item's `source_version` and its `eligibility` after defaults are filled (R-3, R-22).

When an item fails several admission checks, the trace records the earliest applicable code in `contract/reasons.json` order (R-21).

`duplicate_item_id` compares a candidate's id with the non-blank string id of every other candidate, in any batch and whatever that candidate's own outcome, and with the `item_id` of every producer exclusion, in any batch. Each candidate sharing an id is excluded with the earliest code that applies to it, so a schema-invalid copy keeps its schema code and an unauthenticated producer's copy keeps `producer_not_authenticated`.

`protected_tier_changed` applies in the slots whose default tier in `contract/slot-defaults.json` is `protected`. In a slot that only the route's `tier_upgrades` raised, an item may set a lower tier of its own, and it is then not protected. A `tier_upgrades` value at or below its slot's default tier changes nothing: a slot's tier is the higher of its default and the route's value, since the slot defaults set the minimum protection (R-16).

`missing_field:<name>` names a field of the item itself: one of the eight minimum fields, or one its slot requires: `expires` for memory (R-9) and `relevance` for knowledge (R-13). An item without a slot requires no slot-specific field, so it is `missing_field:slot`. A variant missing one of its own fields is `invalid_structure`. A batch entry that is not a JSON object is not an item at all: the snapshot fails its schema and is rejected (R-2, R-17).

`unknown_slot` and `unknown_authority` name a value outside the closed set whatever its JSON type. A slot of `5`, `null` or `["evidence.knowledge"]` is not one of the eleven, and the schema also rejects its type, so two codes apply and R-21 records the earlier one: `unknown_slot`, not `invalid_structure`. The same holds for an authority of `7` or `null`. Such an item names no slot, so its row carries none (R-22). The `admission-reasons` case holds each.

The route lists, under `producers`, the slots each producer may send, and an item in any other slot is excluded with `producer_slot_not_allowed` (R-15). A producer's kind limits its slots further, whatever the route lists. A state item comes only from a producer of kind `state` (R-8), a producer of kind `memory` sends only `interaction.memory` items (R-14), and a producer of kind `retrieval` (R-13) or `mcp` (R-15) only `evidence.knowledge` and `evidence.tool_results` items. Any other item from them is excluded with `producer_slot_not_allowed`. The one exception is a tool specification an `mcp` producer sends to `governance.capabilities` when the route lists that slot for it: R-15's capability check excludes it with `capability_not_allowed`, since only the route's capability policy may emit capabilities. Where the route does not list the slot for it, the tool is `producer_slot_not_allowed`, which comes first in `contract/reasons.json`; the `admission-route-slots` case holds both. That policy is the producer the snapshot's `capabilities.policy_producer` names, and the route must list it with kind `capability_policy`: a `governance.capabilities` item is admitted only from that producer's batch, and only when `capabilities.allowed_ids` holds its id; every other one, including one from the grant's producer when the route lists it with another kind, is `capability_not_allowed`. The `capability-policy-kind` case holds such a grant.

The last admission check is placement (R-20). An item whose slot the profile does not place is excluded with `slot_unplaced`, unless it is protected: a protected item is admitted, and assembly then refuses with `protected_slot_unplaced`. An item is protected when its tier is, which is its own `tier` when it sets one and otherwise its slot's default raised by the route's `tier_upgrades`.

## Timestamps

Every date-time in a snapshot, and `context.assembly_time` in a trace, is `YYYY-MM-DDTHH:MM:SS`, an optional fraction of any length, and then `Z` or an offset `±HH:MM`. Digits are ASCII, `T` and `Z` may be either case, the date must exist in the proleptic Gregorian calendar, hours run 00–23, minutes and seconds 00–59, and offsets reach at most ±23:59. This is RFC 3339 §5.6 without leap seconds, which neither JavaScript's `Date` nor Python's `datetime` can represent, so an instant would have no portable place in the order R-2 compares by. The schemas carry `format: date-time`, which names RFC 3339 and is the rule that decides whether a date exists, and a `pattern` beside it that pins the rest of this shape, because format checkers disagree: ajv-formats accepts a space for `T`, offsets without a colon and second 60, and Python's `rfc3339-validator` accepts a trailing newline. The pattern does not check the calendar, so a validator must assert `format`: Python's jsonschema asserts `date-time` only with `rfc3339-validator` installed, and ajv only with `ajv-formats`. The `admission-reasons` case holds `2026-02-30` as `invalid_structure`, and an implementation that leaves `format` unasserted fails it. The pattern ends in `(?![\s\S])` rather than `$` because Python's `$` also matches before a final newline. For the same reason, schema digests bound their length as well as matching `^[0-9a-f]{64}$`. A profile's `evaluation.date` is a full date, `YYYY-MM-DD`, and its schema pairs `format: date` with a pattern the same way. The `admission-reasons` case holds a leap second, a space separator, an offset without a colon and a trailing newline, each `invalid_structure`.

## Numbers

Every number in a snapshot is an IEEE 754 double, as I-JSON (RFC 7493) expects and as JavaScript's `JSON.parse` reads it (R-2). An assembler reads each number as the nearest double before comparing it with anything: a `relevance` with `min_relevance` or with another `relevance` in a slot's rank, a token count with `token_budget`, `max_tokens`, `min_tokens` or `budget.input`. An integer beyond 2^53 therefore rounds to the same double in every language, and two integers that round to the same double are equal: `9007199254740992` and `9007199254740993` tie, and `9007199254740991` is below both. A language whose JSON parser keeps integers exact, as Python's does, must round them at the boundary. A number outside the double range is rejected before assembly (Snapshot checks), and the digest serializes the rounded value (Snapshot digest). The `threshold-beyond-2-53` case holds such a pair, and `digest-beyond-2-53` holds integers with more than 17 significant digits, which round to a double whose exact value has digits the digest does not write. A number is read as the nearest double however it is written, with a fraction or an exponent included: `doubles-nearest` holds 2^53 written `9007199254740992.0` and halfway values written `9007199254740993.0` and `4503599627370496.5`, which round to even, and `doubles-largest` holds the largest double written `1797693134862315700E290` and `1.7976931348623158e308`, which rounds to it rather than out of range. A parser that is not correctly rounded misreads some of them. An integer written with a zero fraction is the same double, and JSON Schema counts it as an integer, so `integer-written-as-double` caps a slot at `max_per_source: 2.0` exactly as `diversity-cap` caps it at `2`.

## Blank strings

A string is *blank* when every character in it is ECMAScript whitespace or a line terminator: the set `fixture-whitespace/v1` lists under Tokenizers and renderers. R-2's "non-blank string id" is a string with at least one other character, and the schemas' `pattern` for non-blank strings lists that set explicitly rather than writing `\S`, because Python's `re`, which Python JSON Schema validators use, reads `\S` differently at U+001C–U+001F and U+FEFF. So an id of U+FEFF alone is blank and is recorded as `{producer}#invalid-{n}`, and an id of U+001C alone is an ordinary id. The `admission-reasons` case holds both.

## Ordering

Wherever this document orders strings (item, producer and group ids, slot names, field names), it compares them by UTF-16 code units, the order RFC 8785 uses for member names. Shorter strings come first when one is a prefix of the other. JavaScript's default sort already compares this way. Other languages must do so explicitly; in Python, for example, sort by `s.encode("utf-16-be")`. Code-point order, the default in Python, Go and Rust, differs only when a string holds a character outside the Basic Multilingual Plane: U+1F600 sorts before U+FF5A in UTF-16 code units, and after it in code points. The `ordering-astral-ids` case checks this.

Items within a placement go by `id` in this order, with one exception: `interaction.history` renders its turns in the order they were said, by `freshness` compared as instants at full precision, and by `id` only among turns said at the same instant (R-7). The `history-freshness-order` case checks this.

## Snapshot digest

`context.snapshot_digest` identifies the frozen snapshot an assembly used, so a stored snapshot can be replayed and matched to its trace (R-22, R-23). It is the lowercase SHA-256 of the UTF-8 bytes of the RFC 8785 serialization of the *normalized* snapshot. Normalizing reorders only the arrays whose order producers do not control, so the same inputs give the same digest however they arrive:

- `batches` by producer id;
- within a batch, the candidates whose `id` is a non-blank string by `id`, candidates sharing an id by the bytes of their own RFC 8785 serialization, and then every other candidate in the order the batch supplied it, since R-2 numbers those in that order;
- a batch's `excluded` rows by `item_id`, then by the bytes of their serialization;
- `conflicts` by `id`, and each group's `items`.

Every other array keeps its order, including profile placements and route-policy lists such as `precedence` and `fitting_order`, whose order means something. Strings order as Ordering describes. A snapshot's strings must be well-formed Unicode (I-JSON, RFC 7493): a string holding an unpaired surrogate, or a number outside the IEEE 754 double range such as `1e400`, has no RFC 8785 serialization, so the snapshot is rejected before assembly. RFC 8785 serializes every number as a double, so an integer beyond 2^53 is rounded as JavaScript rounds it, and written as JavaScript writes it: the shortest digits that read back as the same double, padded with zeros. `12345678901234567890` is the double whose exact value is 12345678901234567168, and is written `12345678901234567000`; the `digest-beyond-2-53` case holds it. `generators/digest.py` computes the digest, and the website's tests compute it again in JavaScript.

## Refusals

A refused trace has `result: null`, `included: []` and `compressed: []` (R-17). It keeps the producer, admission, conflict, supersession, deduplication and source-diversity rows in `excluded[]`, `conflicts[]` and `defaults_filled[]`: conflicts are resolved right after admission, then stale observations are superseded, duplicates removed and sources capped, all before any refusal check, and none of these ever excludes a protected item, so none can cause `required_slot_missing`. A `slot_floor_over_budget` or `evidence_required` refusal comes after fitting, so it also keeps the fitting rows. Assembly checks the refusal conditions in `contract/reasons.json` order and records the first that holds (R-21):

1. `required_slot_missing`: no admitted item in `governance.instructions` or `interaction.query`, or, on a route with `parser: true`, in `governance.output_contract` (R-4).
2. `protected_slot_unplaced`: an admitted protected item's slot has no placement in the profile (R-20).
3. `conflict_unresolved`: a conflict group escalated, and its action is `request_context` or `refuse` (R-11). `recovery.action` is `request_context` when every such group's action is `request_context`, and the trace has no `recovery` otherwise.
4. `protected_content_over_budget`: a protected item's rendered body exceeds its `token_budget`, the protected items in a slot exceed the slot's `max_tokens`, or the payload rendered from the protected items alone does not fit (R-17). Nothing is shed first, so the trace has no `over_budget` rows.
5. `slot_floor_over_budget`: after fitting, the payload still does not fit because a slot's `min_tokens` withheld a reduction (R-17). It has no `recovery`.
6. `evidence_required`: after fitting, a route with `requires_evidence: true` includes no `evidence.knowledge` or `evidence.tool_results` item, or fewer items in an evidence slot than that slot's `min_included` (R-12). It counts items, so an item the profile places twice counts once. `recovery.action` is:
   - `request_context` when no evidence item was omitted for budget, so the shortfall came from producers or admission;
   - `precompute_summary` when an evidence item omitted for budget had no variants;
   - `retrieve_narrower` otherwise: every evidence item omitted for budget had variants, and they did not fit.

## Conflicts

Conflict resolution runs right after admission (R-6, R-11). It acts only on the groups the application declared, and it never reads a body. A group's *members* are the items it names that admission admitted. The trace's `items` lists every id the group names, in `id` order.

**Moot.** A group with fewer than two members changes nothing: `decided_by: moot`, `resolution: moot`. The steps below decide only groups that are not moot (R-11).

**Instruction groups.**

1. Only `governing` and `user` authority may instruct (R-6). Members with any other authority, `untrusted` included, stay in the payload as material and take no part in the decision. A member's `trust` and `injection_risk` are never read here: a marked history turn with `authority: user` may instruct like any other user member.
2. The *peers* are the members at the highest instructing authority present: `governing`, or else `user`. With one peer, or none, the group is decided by authority, and nothing is excluded: `decided_by: authority`, `resolution: resolved`, and `winner` is that peer when there is one.
3. With two or more peers, if exactly one peer's `conflict_policy` is `governs` and every other peer's is `defers`, the deferring peers are excluded with `conflict_deferred`: `decided_by: policy`, `resolution: resolved`, `winner` the governing peer. Any other combination escalates: two peers that govern, peers that all defer, or any peer whose `conflict_policy` is `escalate`. A lone peer is decided by authority in step 2 whatever its `conflict_policy` says, so `escalate` takes effect only against another peer.
4. Only peers are excluded. A member below the peers, such as a `user` member when governing peers are present, stays in the payload however the peers are decided.

**Fact groups** use the route's `facts[<fact>]` policy.

1. A member is *eligible* when the authenticated producer of its batch appears in `precedence` and its `scope` carries every key the policy's `scope` lists.
2. The *leaders* are the eligible members whose producer comes earliest in `precedence`. A single leader wins: `decided_by: policy`. When there are several, the policy has `freshness_tiebreak: true`, and one leader's `freshness` is strictly later than every other leader's, that leader wins: `decided_by: freshness`. Otherwise, and when no member is eligible, the group escalates.
3. Every other member, eligible or not, is excluded with `conflict_lost`. The result has `resolution: resolved` and `winner` the winning member.

Nothing else decides eligibility or precedence: not a member's `authority`, `trust` or `injection_risk`, and not its producer's `verified` flag (R-11). A route that wants a verified server's output to win lists that producer earlier in `precedence`.

**Protected members.** Resolution never excludes a protected item (R-16's tier, as Fitting defines it). A decision that would exclude one escalates instead, and nothing in the group is excluded.

**Escalation.** An escalated group has `decided_by: escalated` and no `winner`. It takes the fact policy's `on_unresolved`, or for instruction groups the route's `on_unresolved_instruction` (default `refuse`):

| Action | `resolution` | Effect |
| --- | --- | --- |
| `surface` | `surfaced` | Every member stays. The renderer marks each occurrence of a member as conflicting. |
| `request_context` | `context_requested` | Assembly refuses with `conflict_unresolved`. |
| `refuse` | `refused` | Assembly refuses with `conflict_unresolved`. |

Each item excluded by a group adds one `excluded[]` row with its reason, stage `assembler` and its slot. Excluded items take no further part in assembly.

## Supersession

Supersession runs right after conflict resolution and before deduplication, only in the slots whose route rules set `supersede: "source"` (R-25). It considers the items admission admitted and conflict resolution did not exclude.

1. Within one slot, items form a *call* when they share the authenticated producer of their batch and the same `source`, compared exactly. A producer can only supersede its own items: `source` is item-controlled, and R-15 forbids trusting it alone.
2. The *latest* items of a call are those whose `freshness` is the latest instant among the call's items, compared at full precision (R-2). Equal instants tie however they are written: `11:58:00Z`, `11:58:00.000Z` and `13:58:00+02:00` are the same instant. Every latest item is kept.
3. Every other item of the call is excluded unless it is *exempt*, as Deduplication defines it: protected, or named by a conflict group.
4. Each excluded item adds one `excluded[]` row with reason `superseded`, stage `assembler`, its slot and `superseded_by`, the highest-ranked latest item by the slot's rank as Fitting defines it.

Only `source` and `freshness` decide: bodies, variants and `source_version` are not compared. A superseded item takes no further part in assembly and was not omitted for budget, so it does not count toward R-12's recovery action.

## Deduplication

Deduplication runs right after supersession, before any refusal check, and only in the slots whose route rules set `dedupe: "exact"` (R-24). It considers the items admission admitted and neither conflict resolution nor supersession excluded.

1. An item's *key* is its body with every maximal run of whitespace (the set Blank strings defines) replaced by one U+0020, and then any U+0020 at either end removed. Keys are equal only when they are the same sequence of code units: there is no Unicode normalization and no case folding, so `é` (U+00E9) and `e` followed by U+0301 differ, as do `Refund` and `refund`. Implementations must not normalize: runtimes ship different Unicode versions, and would disagree on characters one of them does not yet assign.
2. Within one slot, items with equal keys form a *duplicate set*. Items in different slots are never compared, and a slot without `dedupe` keeps equal bodies.
3. An item is *exempt* when it is protected (its tier, as Fitting defines it) or a conflict group names it, whatever the group's resolution.
4. A duplicate set with an exempt member keeps every exempt member and excludes the rest, naming its highest-ranked exempt member in `duplicate_of`. A set without one keeps its highest-ranked member and excludes the rest, naming that member. Rank is the slot's rank as Fitting defines it: its `order_by` keys, then `id`.

Deduplication compares bodies only. It ignores variants, and a kept item keeps its own. Near-duplicates are the retriever's to find: one that drops a chunk as a near-duplicate reports it in its batch's `excluded` list as `duplicate_content` with `duplicate_of` (R-13), and the trace carries that producer row as reported, ahead of the assembler's rows. Each excluded item adds one `excluded[]` row with reason `duplicate_content`, stage `assembler`, its slot and `duplicate_of`, and takes no further part in assembly. It was not omitted for budget, so it does not count toward R-12's recovery action.

## Source diversity

The source diversity cap runs right after deduplication, before any refusal check, and only in the slots whose route rules set `max_per_source` (R-26). It considers the items that neither conflict resolution, supersession nor deduplication excluded.

1. Within one slot, items share a *source* when they share the authenticated producer of their batch and the same `source`, compared exactly, as Supersession groups a call.
2. A source keeps its *exempt* items (protected, or named by a conflict group, as Deduplication defines it), which take places first.
3. Its other items then fill the places left, up to `max_per_source`, from the highest rank down, by the slot's rank as Fitting defines it. A source with as many exempt items as the cap, or more, keeps no other item.
4. Each item left over adds one `excluded[]` row with reason `source_diversity_cap`, stage `assembler` and its slot.

A capped item takes no further part in assembly and was not omitted for budget, so it does not count toward R-12's recovery action. The cap groups chunks only as well as producers name their sources: a retriever should set `source` to the document a chunk comes from, not to the chunk.

## Fitting

Fitting reduces the admitted items the profile places, less any that conflict resolution, supersession, deduplication or the source diversity cap excluded, until the payload fits (R-16). The payload *fits* when its *charged* count is at most `budget.input`. The charged count is the whole payload, rendered and counted with the declared tokenizer, times (100 + `budget.margin_percent`) / 100 and rounded up to an integer; an absent margin is 0, so the charged count is then the count itself. Integer arithmetic gives it exactly: `(n × (100 + m) + 99)` divided by 100, discarding the remainder. Only this test takes the margin. `token_budget`, `max_tokens` and `min_tokens` compare unscaled counts, because they share the payload out rather than bound it, and `included[]`, `compressed[]` and `result.input_tokens` record unscaled counts. The trace's `budget` repeats `margin_percent` when the snapshot sets it. An implementation may estimate, but it must reach the same decisions. An item's tier is its own `tier` when it sets one, and otherwise its slot's default raised by the route's `tier_upgrades`.

1. If a protected item's rendered body exceeds its `token_budget`, the protected items in a slot exceed the slot's `max_tokens`, or the protected items alone do not fit, refuse with `protected_content_over_budget`.
2. Enforce the other items' `token_budget` caps, in shedding order, whether or not the payload fits. A droppable item whose rendered body exceeds its cap is omitted. A compressible one takes the variant with the most tokens whose rendered body is within the cap, the earlier one on ties, and is omitted when there is none. A `null` cap sets no per-item limit.
3. Enforce the route's slot caps, whether or not the payload fits. For each slot with `max_tokens`, in shedding order, reduce the slot's own items while its *size* exceeds `max_tokens`, as steps 4 and 5 reduce the payload, with "the slot is within its cap" in place of "the payload fits" and no slot floors: omit its droppable items one at a time, from the lowest rank up, and then run the steps for that slot, which are the route's `fitting_order` steps that name it, then its `compress` step and its `omit` step unless the route listed them. A slot without `max_tokens` has no cap.
4. While the payload does not fit, omit droppable items one at a time, in shedding order.
5. While it still does not fit, reduce compressible items step by step. The route's `fitting_order` steps come first. Then come a `compress` step for each slot, in shedding order, and an `omit` step for each slot, in shedding order, skipping any step the route listed. A step visits the slot's compressible items from the lowest rank up and stops as soon as the payload fits.
   - `compress` replaces an item's body with a supplied variant whose rendered body has fewer tokens than its current one: its own body, or the variant a cap or an earlier step chose. It picks the variant with the most tokens that makes the payload fit, or, when none does, the one with the fewest. Among variants with equal counts, the earlier one in `variants` wins. An item with no shorter variant is left as it is.
   - `omit` removes the item, compressed or not.
6. Protected items are never compressed, truncated or omitted.
7. If the payload still does not fit, refuse with `slot_floor_over_budget`. Only a slot floor can leave it so.

*Slot floors* hold during steps 4 and 5, and only then. Before an omission or compression in a slot whose route rules set `min_tokens`, compute the slot's size as the reduction would leave it. If that is below `min_tokens`, the reduction is not made, and the slot is *frozen*: steps 4 and 5 make no further reduction to any of its items, even a smaller one that would have stayed above the floor. The reduction tested is the one the step would make: for `compress`, the variant chosen as above. A slot whose size is already below `min_tokens` is frozen by its first reduction, so it is shielded whole. A frozen slot keeps its droppable items while other slots reduce compressible ones, which is the one exception to shedding droppable items first; within the slot, tier order still holds. Floors do not guard steps 2 and 3, so a slot whose `max_tokens` is below its `min_tokens` is capped first and then shielded.

A slot's *size* is the sum of `included[].tokens` over the slot's rows: the tokens of its items' rendered bodies, each occurrence counted as it renders. A slot the profile places twice counts both occurrences, so its `max_tokens` and `min_tokens` bound them together.

*Shedding order* takes slots by ascending `priority` (default 0), then by slot name, and within each slot takes items from the lowest rank up. Rank sorts by the slot's `order_by` keys, then by `id`, with the first item ranked highest. The default keys are `["-relevance", "-freshness"]`: higher scores rank first and unscored items last, then newer items first.

Fitting treats a member of a surfaced conflict group like any other item: it may omit one, with an `over_budget` row, and the members it keeps still render marked as conflicting, since the conflict was real (R-11). The `conflict-surfaced-shed` case checks this.

Fitting decides per item. A slot the profile places twice sheds or compresses both occurrences together. When those placements render a body differently, as `system` and an `xml:` wrap do in `cwa-messages/v1`, the size of the item's body or of a variant, wherever this section compares one with a cap or with another, is the largest of its occurrences' renderings: a cap bounds the body however it is rendered. Each omitted item adds one `excluded[]` row with reason `over_budget`, stage `assembler` and its slot. Each included occurrence of a compressed item adds one `compressed[]` row: `from` counts the original body and `to` and `included[].tokens` the variant, each as that occurrence renders it, and `method` and `variant_id` name the variant (R-18).

*Cost.* Every reduction in steps 4 and 5 is its own fit test, and every fit test counts the whole payload. Work therefore grows with the number of reductions times the payload's size, and becomes quadratic when most candidates are shed: the reference assembler tokenizes about 49 million characters, in about a third of a second, when budget pressure sheds 498 of 500 chunks. An implementation may reach the same decisions faster, but no shortcut may change one; that rules out, for example, adding up the counts of an item's parts where the tokenizer does not count the whole as the sum of its parts. Keep the cost down at the source: a retriever sends no more chunks than the route's budget can use, and a route can bound a slot before budget pressure: `max_per_source` (R-26) drops surplus chunks without counting anything, and `max_tokens` (R-16) measures only the slot's own items.

## Snapshot checks

A snapshot is *valid* when it satisfies `snapshot.schema.json`, and the schemas it references, and passes every check below. An invalid snapshot is rejected before assembly, with no payload and no trace, because its profile, budget or context may be missing or contradictory (R-17). Rejection reports the application's error in building the snapshot. An implementation lists the problems in its own words, since no reason code names them; the codes in `contract/reasons.json` describe assemblies of valid snapshots, refusals included.

- **I-JSON (R-17).** No string holds an unpaired surrogate, and every number, an integer literal of any length included, rounds to a finite IEEE 754 double, so the snapshot has an RFC 8785 serialization (Snapshot digest).
- **One batch per producer (R-15).** No producer id heads more than one batch. A batch is one authenticated producer's output for the call (R-15), and rows, ranks, supersession and source diversity all key on that producer.
- **Conflict groups (R-11).** Group ids are unique, every item id a group names is the id of a candidate or a producer exclusion in the snapshot, no item belongs to two groups, and a fact group's `fact` is a key of the route's `facts`.
- **Producer exclusions (R-9, R-13).** An exclusion's `duplicate_of` or `superseded_by` is the id of a candidate in the same batch. Its `reason` is an exclusion code, which the batch schema checks.
- **Profile (R-19, R-20).** Its `spec` is `cwa/draft`, which the profile schema fixes and the trace repeats as `context.spec` (R-21). Its `route` and `route_policy_version` equal the route policy's `route` and `version`. It places `governance.instructions` and `interaction.query`, and `governance.output_contract` when the route sets `parser: true`. The snapshot's renderer can realize it (Tokenizers and renderers).

A tokenizer or renderer the implementation does not provide is not a problem with the snapshot, so the snapshot is not rejected for it. A case that uses an optional one is skipped, and one that uses a required one has failed (Reporting results).

## Tokenizers and renderers

Every implementation provides the tokenizers and renderers below, before Optional, and every published case uses them or one listed under Optional. Without the two fixtures an assembler's report could back its claim (§1 on the spec page) with few cases or none, without `estimate-utf8/v1` the only published tokenizer meant for a model would go untested, and without `cwa-messages/v1` so would the platform roles R-7 keeps with the application. A tokenizer or renderer published after these is optional unless it is added to them. Optional lists them, and a case that uses an optional one the implementation does not provide is skipped (Reporting results).

An application may declare a tokenizer of its own instead (§1 on the spec page). It counts a text as a non-negative integer, reading nothing but that text (R-23), under an ID no published tokenizer uses, so a trace that names a published one always means its published count. An application may also hand an assembler a renderer of its own, though it then renders with one no case covers, which §1 does not allow a conformant application. An assembler does not accept an application's tokenizer under the ID of a published tokenizer, or its renderer under the ID of a published renderer, including one the assembler does not provide itself: it stops before assembly, with no payload and no trace (R-16). No case can supply a component of its own, so no report covers these rules, and each implementation tests them itself.

- `fixture-whitespace/v1` counts maximal runs of characters outside the ECMAScript whitespace and line-terminator set: U+0009–U+000D, U+0020, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000 and U+FEFF. This is what JavaScript's `/\S+/gu` matches. Other languages must use this set explicitly; Python's `\S`, for example, differs at U+001C–U+001F and U+FEFF. It is a test fixture, not a model tokenizer.
- `estimate-utf8/v1` counts a text as the number of bytes in its UTF-8 encoding divided by 4, rounded up: `(bytes + 3)` divided by 4, discarding the remainder, so an empty text counts 0. It is a portable estimate for models whose provider offers no local tokenizer, close to English text on common BPE vocabularies and low for scripts that take several bytes a character but about one token each, such as Chinese and Japanese. Pair it with a `budget.margin_percent` that covers the error for the route's text (R-16). A snapshot is already free of unpaired surrogates, so every text has one UTF-8 encoding.
- `fixture-xml/v1` renders each placed item as `<{tag} id="{id}">\n{body}\n</{tag}>\n`, where `{tag}` is the placement's `wrap` without its `xml:` prefix, in profile placement order. Within a placement it orders items by `id`, except `interaction.history`, whose turns it orders by `freshness` and then `id` (R-7). A member of a surfaced conflict group renders as `<{tag} id="{id}" conflict="{group id}">` instead, with the same body and closing tag. It escapes `&`, `<` and `>` as `&amp;`, `&lt;` and `&gt;` in bodies, and additionally `"` as `&quot;` in attribute values. It supports only `xml:` wraps, where the tag matches `[A-Za-z_][A-Za-z0-9_.-]*` (ASCII only). Per-item `tokens` count the rendered body; wrapper tokens appear only in `result.input_tokens`, which counts the whole payload text.
- `cwa-messages/v1` renders the payload as a message request, so the platform's roles stay with the application (R-7). Its payload is the RFC 8785 serialization, in UTF-8, of an object with three members:
  - `system`: one entry per occurrence placed with wrap `system`, in placement order and by `id` within a placement. An entry is `{"id": item id, "text": body}`, with the body unescaped, since only verified governance content with no injection risk reaches a governance slot (R-10). A member of a surfaced conflict group also has `"conflict": group id`, and its `text` is `<conflict group="{group id}">\n{body}\n</conflict>`, the group id escaped as `fixture-xml/v1` escapes attribute values. An application hands the model each entry's text and nothing else (§1 on the spec page), so the mark has to be in the text for the model to see it (R-11).
  - `tools`: one entry per occurrence placed with wrap `tools`, built the same way.
  - `messages`: exactly one message, `{"role": "user", "content": text}`. `text` holds every occurrence placed with an `xml:` wrap, in placement order and, within a placement, in `fixture-xml/v1`'s item order, rendered exactly as `fixture-xml/v1` renders it, with one addition: an `interaction.history` occurrence has ` speaker="assistant"` after its `id` attribute when the item has `lineage: generated`, and ` speaker="user"` otherwise, before any `conflict` attribute. Prior turns are part of this transcript and never become messages of their own; the query is the only live user turn (R-7).

  A profile is realizable only when each `wrap` is `system`, `tools` or an `xml:` wrap with a valid tag; `system` is used only on governance slots and `tools` only on `governance.capabilities`, since no other slot may take a platform role (R-7); and every `system` placement comes before every `xml:` placement, because a message request cannot put material ahead of its system text. An unrealizable profile is rejected with the snapshot, before assembly. `result.input_tokens` is the sum of the tokenizer's counts of every entry's `text` and of the message's `content`; role names, ids and JSON punctuation are not counted, since the renderer does not emit them as text, and a route leaves room for them with `budget.margin_percent` (R-16). Per-item `tokens` count the rendered body: unescaped in `system` and `tools`, escaped in the message. A conflict mark's `<conflict>` wrapper, like an `xml:` wrapper, counts only in `result.input_tokens`. `result.hash` is the SHA-256 of the payload bytes.

Wherever this document counts the payload, in `result.input_tokens` and in every test of whether the payload fits, it means the renderer's count.

### Optional

A tokenizer or renderer in this list was published after the ones above. An implementation may leave it out, and a case that uses one it does not provide is skipped (Reporting results). An assembler still stops on an application component under its ID (R-16).

- `cwa-message-blocks/v1` renders the request `cwa-messages/v1` renders, except that the user message's `content` is an array with one entry per occurrence placed with an `xml:` wrap, in the same order. An entry is `{"id": item id, "text": rendered}`, where `rendered` is that occurrence exactly as `cwa-messages/v1` writes it into its text. A member of a surfaced conflict group also has `"conflict": group id`, as system entries do, and its mark stays in the text. Joined in order, the entries' texts are the text `cwa-messages/v1` renders for the same included items. The entries are content parts of the one user message, never messages of their own (R-7).

  One entry per occurrence lets an application put a provider's cache breakpoint at any item boundary. Because each prior turn ends an entry and a new turn lands after the earlier ones (R-7), the boundary a breakpoint marked on one call still exists on the next, when the history has grown.

  It realizes exactly the profiles `cwa-messages/v1` realizes. `result.input_tokens` is the sum of the tokenizer's counts of every entry's `text`, whether system, tool or message; entry boundaries and ids are not counted, as roles are not. A tokenizer that does not count a whole as the sum of its parts, such as `estimate-utf8/v1`, can therefore count more here than under `cwa-messages/v1` and fit fewer items; the `blocks-budget` case holds one. Per-item `tokens` count the rendered body as in `cwa-messages/v1`, and `result.hash` is the SHA-256 of the payload bytes. An application hands the entries over as separate content parts of the one user message, or joined in order.

## Registry

A registry holds the profiles and route policies an application assembles with, each pinned in a lock that validates against `schema/registry_lock.schema.json`. Profiles follow R-19 and R-20; route policies are versioned wherever the requirements say "versioned route policy", as R-3, R-6 and R-16 do. It works before snapshots are built, outside assembly: a snapshot carries the profile and route policy the registry returned.

- **Digests.** A profile's digest is the lowercase SHA-256 of the RFC 8785 serialization of the profile without its `evaluation` member, so a change of evaluation status alone keeps the digest, and may keep the version (R-20). A route policy's digest covers the whole policy.
- **Loading.** Every profile and route policy a registry is given must be valid against its schema, and must match a lock entry with the same identity (`id` and `version` for a profile, `route` and `version` for a route policy) and the same digest. Loading fails when an entry has the same identity and another digest, because the content changed without a version increase. It also fails for content with no entry, and for a lock that lists an identity twice.
- **Locking.** Locking adds an entry for each identity not yet pinned. It refuses content whose identity is already pinned with another digest, so the author must increase the version instead. It never rewrites an entry.
- **Deployment.** An application deploying a profile asks for it in deployment mode, which returns only a profile with `evaluation.status: evaluated`. The profile schema then requires a concrete `model_family` and the evaluation's `suite`, `date`, `result` and `artifact` (R-19). Draft use, such as development and these conformance cases, may load unevaluated profiles. A profile's digest covers `model_family`, so promoting a draft that has `model_family: null` changes its model target and needs a new version (R-20); only a profile that already names its model can be promoted at the same version, by changing `evaluation` alone.

`registry/` holds the published example profiles, four conformance route policies, the illustrative route policies the example profiles name (`examples/route-policies.json`) and a lock that pins them all, so that implementations can check they compute the same digests. `generators/registry.py` builds it.

## Reporting results

An implementation reports a run as `conformance-report.json`, valid against `schema/conformance_report.schema.json`. The report names the implementation, and the repository and commit its cases came from, and holds one entry per directory under `cases/`, ordered by id, with the `rules` from that case's `case.json` and one outcome:

- `passed`: the payload and trace match, as Running a case describes;
- `failed`: anything else, including an exception or a trace the schema rejects. `detail` says what differed;
- `skipped`: the case uses an optional tokenizer or renderer the implementation does not provide. `detail` names it. A case that uses only required ones is never skipped: an implementation that lacks one reports the case as `failed`.

It also holds one entry per directory under `rejections/`, ordered by id, in `rejections`, with the case's `rules` and one outcome:

- `rejected`: the implementation rejected the snapshot before assembly, with no payload and no trace;
- `failed`: anything else: it assembled a payload, refused, or raised something other than a rejection. `detail` says what happened;
- `skipped`: the case uses an optional renderer the implementation does not provide, and the check the case breaks is that renderer's, as it is in `profile-unrealizable`, `profile-invalid-tag`, the `messages-*` cases and `blocks-system-after-xml`. Only the last uses an optional renderer. `detail` names it. Every other check runs before a renderer is needed and no check needs a tokenizer, so no other rejection case is skipped, and neither is one whose renderer is required.

Only `passed` and `rejected` count. A report without `rejections` has not run them. A trace that validates against `schema/trace.schema.json` but differs from the expected one has failed: schema validation alone is not conformance (R-21). `implementations/` holds the report of each listed implementation, today the Python reference assembler (beside its `status.json`), the TypeScript assembler, the Go assembler and the Rust assembler, and the Assembler page shows them. A report counts a case only as the case is now: the import records a digest of each case's files at the report's `contract.commit`, and a case published or changed since then counts as not passing until the implementation runs it again.

To list an implementation, run `python3 conformance/import_report.py <its checkout> <id> --label <Language>` in a checkout of this repository and open a pull request with the files it writes under `implementations/`. The checkout must be clean and its report must name a commit of this repository. CI checks the entry, and that the stored report is the `conformance-report.json` the implementation's repository publishes at the stored commit (`import_report.py --verify`). A report is the implementation's own claim (SPEC.md §1); listing it records that claim, it does not re-run it. The Assembler page shows the entry once the website takes that commit.

Implementations vendor these cases pinned by hash, so a case changes only through a reviewed edit here.
