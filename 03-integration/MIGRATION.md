# Migrating the account assistant to CWA

Work in `after/`. It starts as a copy of `before/`. Run the tests against your work with `CWA_W3_IMPL=after uv run pytest`; they fail step by step until the migration is done. `uv run pytest` runs them against `solution/`, which is a reference to read when stuck, not to copy blind.

The six steps are the Start page's six, applied to this application. Each step names the tests that go green when it is done.

## Step 1. Name the slots you already send

Read `before/app.py`'s `build_request()` and fill in [inventory.md](inventory.md): every piece of text the old prompt concatenates, which slot it belongs to, what authority it carries, where its source and version would come from, and which of the seven failure modes it is exposed to. Then list every "never" or "always" sentence in `before/instructions.md`: those are candidates for step 6.

Nothing changes in the code yet. **Tests:** none.

## Step 2. Freeze a snapshot and hand it to an assembler

In `after/context.py`, write `snapshot(request)` and `assemble(document)`. The snapshot has `assembly_time` (the request's `asked_at`), `scope` (tenant, user, session), `budget`, `profile`, `route_policy`, `tokenizer`, `renderer`, `batches` and `conflicts`. It can be built with placeholder policy files and empty batches first; it will be rejected, and the problems the assembler lists are your to-do list.

In `after/app.py`, replace `build_request()` so it returns `(document, result)` by freezing and assembling, add `provider_request(result)` that returns `provider.request_for(payload, model, reserved_output)` or `None` on a refusal, and make `main()` print the decisions and send the provider request.

**Tests:** `test_build_request_freezes_and_assembles`, `test_the_same_snapshot_renders_the_same_bytes`.

## Step 3. Give every item an authority and a source

In `after/producers.py`, write the five producers. You wrote them in W2 and W9 module A; what is new is that `accounts_db` and `memory_store` also return the facts their items assert, and `context.conflict_groups(facts)` turns two claims about the same fact into a declared group. The assembler never reads the bodies to find a contradiction (R-11).

Scope keys go on every item that has them: tenant and user on account and memory items, session on turns. The memory producer honours the `memory-store-ignores-user` fault so the scope test can inject a leak and watch the assembler catch it.

**Tests:** `test_every_item_has_an_authority_and_a_source`, `test_a_missing_field_is_excluded_not_guessed`, `test_a_conflict_is_declared_and_decided_by_policy`, `test_scope_catches_a_producer_leak`.

## Step 4. Check the trace

Run `uv run python -m after.app --conversation scenarios/01-ada-export/conversation.json` and read the table. Then the two checks the Start page asks for: replay the stored snapshot with `--replay` and compare the hash; remove `relevance` from a chunk in a copy of the snapshot and watch `missing_field:relevance` appear. Both are tests already; this step is reading them with your own eyes.

**Tests:** the step 2 and 3 tests again; `test_the_off_topic_question_refuses_and_nothing_is_sent`.

## Step 5. Pick a placement profile and set the budget

Write `after/policy/route-policy.json`, `profile.json` and `assembly.json`. The route policy lists the five producers with their kinds and slots, the slot rules (a relevance threshold, `min_included: 1` and `requires_evidence: true` so an unanswerable question refuses, a `max_tokens` on history, `required_scope` keys, the `turn:` prefix on memory), `tier_upgrades` making `state.user` protected, a `facts.plan` entry with `accounts-db` before `memory-store`, and a `fitting_order`. The profile places the six slots and carries `version: 1` and an `unevaluated` evaluation object. `assembly.json` holds the model's context limit and the reserved output; `context.budget()` computes `budget.input` from them (R-16).

**Tests:** `test_budget_input_is_the_context_limit_less_reserved_output`, `test_the_profile_is_versioned_and_matches_the_route`, `test_history_is_capped_by_the_route`, `test_the_payload_is_handed_over_unchanged`.

## Step 6. Move enforcement out of the prompt

In `after/guards.py`, write `no_unverified_prices` and `only_the_signed_in_workspace`. They run on the reply against the evidence the assembler included and the request's tenant. Wire `guards.check()` into `after/app.py`'s `answer()` so a failing decision withholds the reply. The sentences stay in `instructions.md`: guidance in context, invariants outside the model (R-5).

**Tests:** `test_the_price_guard`, `test_the_workspace_guard`.

## Done

`CWA_W3_IMPL=after uv run pytest` is green. Diff `before/app.py` against `after/app.py` and write the application conformance list in [inventory.md](inventory.md): which of the application's duties (§1 of the spec) the app now meets, and which remain open.
