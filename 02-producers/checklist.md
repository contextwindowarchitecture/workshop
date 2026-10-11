# Producer conformance checklist

One page for code review. A producer's conformance claim rests on its own word, so this is what a reviewer checks. Each line names the requirement and the reason code the assembler records when the line is broken; the linter (`lint.py`) catches the lines marked L, the trace catches them all.

## The batch

- [ ] One batch per producer per snapshot; the application adds `producer: {id, kind}` when it freezes (R-15). Two batches from one producer reject the snapshot.
- [ ] Every id is unique across the whole snapshot, not just this batch (R-2, `duplicate_item_id`). L
- [ ] Every entry the producer suppressed is an `excluded` row `{item_id, reason, stage: "producer"}` with a reason from `contract/reasons.json` (R-9). A bad reason rejects the snapshot. L
- [ ] A `duplicate_content` row carries `duplicate_of`, a `superseded` row carries `superseded_by`, and each names a candidate in this same batch (R-13, R-25). L
- [ ] No suppressed entry's body appears anywhere in the batch (R-14).

## Every item

- [ ] The eight required fields: `id`, `slot`, `source`, `source_version`, `authority`, `freshness`, `trust`, `body` (R-2, `missing_field:<name>`). L
- [ ] No undeclared field: the schema is closed (R-2, `invalid_structure`). L
- [ ] `freshness` is when the content was observed or true, RFC 3339, not later than assembly plus the route's clock skew (R-2, `future_freshness`). It is never an expiry.
- [ ] `slot` is one of the eleven and `authority` is the one that slot takes; `untrusted` only in tool results, memory and history (R-1, `authority_not_allowed`). L
- [ ] The slot is one the producer's kind may address, whatever the route lists (R-13, R-14, R-15, `producer_slot_not_allowed`). L
- [ ] `scope` carries every key the route's `required_scope` lists for the slot; a missing key is never a wildcard (R-2, `out_of_scope`). L
- [ ] `source` starts with the route's `source_prefix` for the slot, where one is set (R-3, `source_invalid`). L
- [ ] `tier` is absent, or not above the slot's default; in a protected slot it is not below (R-16, `tier_upgrade_not_allowed`, `protected_tier_changed`). L
- [ ] The six policy fields are set deliberately or left to the slot defaults on purpose; whichever you choose, `defaults_filled` in the trace is what you expect (R-3).
- [ ] Each variant has its own `id`, `body`, `method` and `lineage`; no variant repeats an id or reuses the item's; every variant is shorter and adds no instruction or fact (R-18, `duplicate_variant_id`). L
- [ ] Variants and scores were computed before the request and are cached by content hash (R-18).

## By slot

- [ ] `evidence.knowledge` and `evidence.tool_results`: one item per chunk or observation, never a merged blob; every knowledge item carries `relevance`; `injection_risk: untrusted_content` (R-13, R-10, `missing_field:relevance`, `untrusted_content_unmarked`). L
- [ ] `interaction.memory`: `expires` on every item, `source` names the turn, only `generated` or `untrusted` authority; expired and revoked entries are reported, not sent (R-9, R-14, `expired`, `revoked`). L
- [ ] `state.*`: written by the application from its system of record, `freshness` is the read time, `injection_risk: none`; the route's `max_age_seconds` decides staleness (R-8, `stale_state`).
- [ ] `governance.*`: `trust: verified` and `injection_risk: none`, or the governance gate excludes it (R-10, `untrusted_in_governance`). L
- [ ] `governance.capabilities`: only the capability policy producer the grant names emits here; an MCP adapter proposes tool specifications to it and never emits them (R-15, `capability_not_allowed`).
- [ ] `interaction.history`: a prior model turn carries `untrusted` authority and `generated` lineage; every turn carries the injection marker (R-1, R-7, R-10).

## What the producer does not do

- [ ] It does not filter by relevance, cap by source, drop exact duplicates or trim to a budget. Those are the route's rules, so the trace can show them (R-3, R-16, R-24, R-26).
- [ ] It does not call a model during a request, and it does not write variants during a request (R-18).
- [ ] It does not prove its own identity: `source` and `trust` are claims; the application binds the producer id outside the items (R-15).
