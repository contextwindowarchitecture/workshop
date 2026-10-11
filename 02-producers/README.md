# W2. Building a conformant producer

Half a day, self-paced, model-free. You leave with three producers you wrote, a test suite that asserts their batch shape and the reason codes they must never trigger, and a one-page checklist for reviewing anyone else's.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` here fetches the reference assembler at its `draft-release` tag; nothing else is installed and no sibling repository is read.
- Finish W1, or at least be able to read a decisions table: `+` included, `~` compressed, `-` excluded with a reason and a stage.
- Open [worksheet.md](worksheet.md) beside this file and [checklist.md](checklist.md) for the end.
- The vendored producers guide is at `shared/contract/cwa/guides/producers.md`. The labs cite it by section.

Conference cut (90 minutes): part 1, Lab A, Lab D.

## What a producer is

A producer is anything that proposes items for slots: a retriever, a memory store, a state service, an MCP adapter, the capability policy, the application's own instructions, the conversation. It emits one batch per request, `{items, excluded}`, and the application stamps the batch with the identity it authenticated, `producer: {id, kind}`, when it freezes the snapshot (R-15). Nothing in an item proves who sent it. `source` and `trust` are the producer's claims.

The spec's seven kinds, and the slots each may address whatever the route lists:

| Kind | Slots | Gate requirement |
| --- | --- | --- |
| retrieval | evidence.knowledge, evidence.tool_results | R-13 |
| memory | interaction.memory | R-14 |
| state | state.user, state.task | R-8 |
| mcp | evidence.knowledge, evidence.tool_results; proposes to governance.capabilities, never emits there | R-15 |
| capability_policy | governance.capabilities | R-15 |
| policy, interaction | whatever the route lists, except state slots and capabilities | R-15 |

A producer proposes. It never decides what fits: thresholds, caps, dedupe and the budget are the route's rules, so every item the assembler leaves out is a row in the trace with a reason. The producer's own duties are the first four of the eight stages: rewrite, retrieve, rerank, package. It reports what it suppressed, and it computes its scores and variants before assembly, because assembly never calls a model (R-18).

A **conformant producer** emits only items that meet the item rules (R-1, R-2), reports every entry it suppresses (R-9), precomputes scores and variants (R-18), and meets the rules for its kind. The claim rests on its word. Admission catches some breaches; others, such as a merged blob that was two chunks, or a chunk silently dropped and never reported, it cannot see. That is why the checklist exists.

## Part 1. Two producers you are given (20 minutes)

Read [fixed.py](fixed.py). It holds the two producers this route needs that are not a lab: `app-policy`, which emits the route's instructions into `governance.instructions`, and `chat-session`, which emits every prior turn into `interaction.history` and the live question into `interaction.query`.

Then run the finished route once, so you know what the end looks like:

```sh
uv sync
uv run freeze.py --user u_ada --history --defaults "How do I export the whole workspace, including attachments?"
```

Read the table. Five producers ran. Three rows carry stage `producer`: the retriever reported a near-duplicate it dropped, and the memory store reported an expired and a revoked memory. The assembler then excluded two chunks below the route's threshold and one exact copy. The last line says `defaults filled: 0`, because every producer here declares its policy fields instead of leaving them to the slot defaults.

**Checkpoint 1.** In the worksheet, record how `app-policy` and `chat-session` set `authority`, `trust`, `injection_risk` and `lineage` on a governance item and on a prior model turn, and why each differs.

## Lab A. A retrieval producer (60 minutes)

Open [labs/retrieval.py](labs/retrieval.py). Its docstring is the specification for `help_center_search()`. The retrieval itself is given: `common.bm25(request.question)` scores every paragraph of the nine Fernway help-centre articles in `shared/fixtures/help-center/`. Your job is everything after the score.

Work until these pass:

```sh
CWA_W2_IMPL=labs uv run pytest tests/test_lab_a.py
CWA_W2_IMPL=labs uv run lint.py
uv run freeze.py --impl labs --user u_ada --history "How do I export the whole workspace, including attachments?"
```

The corpus is rigged to teach. `exports-faq.md` repeats one paragraph of `data-export.md` word for word, and rewords another. Your producer drops the reworded one and reports it as `duplicate_content` with `duplicate_of` naming the chunk it kept (R-13). It leaves the exact copy in, because the route sets `dedupe: exact` and the assembler will exclude it (R-24). In the finished trace both decisions stand side by side, one at stage `producer`, one at stage `assembler`.

Variants come from `data/variants.json`, written ahead of time by `variants.py` and keyed by the SHA-256 of each paragraph. Run `uv run variants.py --check`, then read the file. The shorter form is each paragraph's first sentence, so its lineage is `extracted`, not `summarised`: nothing was written, only cut. W4 replaces this with reviewed model-written summaries stored under the same key.

When the tests pass, do two more things. Remove `lineage` from your items and run `freeze.py --impl labs --defaults`; watch `defaults_filled` grow by one row per item, and put it back. Then squeeze: `freeze.py --impl labs --budget 600 ...` and watch the assembler swap in your variants (`~` rows) before it omits anything (R-16, R-18).

**Checkpoint 2.** The worksheet's Lab A counts, and the sentence on why the variant's lineage is `extracted`.

## Lab B. A memory producer (40 minutes)

Open [labs/memory.py](labs/memory.py). `shared/fixtures/memories.json` holds eight memories across three users. For Ada, one is revoked and one has expired; your producer sends neither body and reports both by id (R-9, R-14). Every memory you do send carries `expires`, a `turn:` source and its own `scope`.

```sh
CWA_W2_IMPL=labs uv run pytest tests/test_lab_b.py
uv run freeze.py --impl labs --user u_cho "Can I get a refund on a monthly plan?"
uv run freeze.py --impl labs --user u_ben --fault memory-store-ignores-user "Which plan are we on?"
```

The last command injects a bug: your producer stops filtering by user and sends Ada's memories for Ben's request. Because each memory carries its own `scope`, the assembler excludes them as `out_of_scope` (R-2), and the trace shows exactly which store leaked. Scope on the item is not redundancy. It is the thing that makes a producer bug visible instead of silent.

**Checkpoint 3.** The worksheet's four memories: what your producer did with each and what the trace shows.

## Lab C. A state producer (30 minutes)

Open [labs/state.py](labs/state.py). `shared/fixtures/accounts.json` is the system of record for workspaces and members. Your producer emits one typed item per fact into `state.user`, with `freshness` set to when the row was read, not when the plan last changed (R-8).

```sh
CWA_W2_IMPL=labs uv run pytest tests/test_lab_c.py
uv run freeze.py --impl labs --user u_ada "Who can change our billing details?"
uv run freeze.py --impl labs --user u_ada --read-at 2026-10-01T09:50:00Z "Who can change our billing details?"
```

The second run uses an account row read ten minutes before the question. The route admits state for 300 seconds, so both items are excluded as `stale_state`. That is the correct outcome: a cached account read is not current state, and the application should read again rather than send it.

**Checkpoint 4.** The worksheet's Lab C lines, including why the code is `stale_state` and not `not_eligible`.

## Lab D. Five items wrong in exactly one way (40 minutes)

Open [labs/negative.py](labs/negative.py). Each function returns one evidence item that the assembler will exclude with exactly the code `EXPECTED` names, and nothing else wrong with it:

| Function | Code | Requirement |
| --- | --- | --- |
| claims_protected | tier_upgrade_not_allowed | R-16 |
| wrong_slot | producer_slot_not_allowed | R-13 |
| unmarked | untrusted_content_unmarked | R-10 |
| reused_id | duplicate_item_id | R-2 |
| no_relevance | missing_field:relevance | R-13 |

```sh
CWA_W2_IMPL=labs uv run pytest tests/test_lab_d.py
CWA_W2_IMPL=labs uv run lint.py --negatives
```

The test adds each item to a valid snapshot and checks that the trace records that code for it and that nothing else changed. "Exactly one way" matters: `shared/contract/cwa/contract/reasons.json` is in precedence order, and an item wrong in two ways gets the earlier code (R-21). `reused_id` is the interesting one: both items sharing the id are excluded, the original too. Then compare what `lint.py` caught with what the trace recorded. The linter runs the checks a producer can run alone; it cannot see across batches, read the clock or know the route's threshold, which is why its last line says what it says.

**Checkpoint 5.** The worksheet's five rows and the sentence on precedence.

## Part 6. The checklist, and your own producer (20 minutes)

Read [checklist.md](checklist.md) against the three producers you wrote. Every line should be something you did on purpose. Then pick one real retriever, memory store, state service or tool in your own system and fill in the worksheet's last section: its kind, the slots it may address, and the checklist lines it will have the hardest time meeting.

**Checkpoint 6.** The worksheet's last section.

## After this workshop

- W9 module A wraps an existing tool, library or MCP server as a producer instead of writing one from scratch; the checklist is the acceptance test.
- Convert the producer you named in checkpoint 6 and open a pull request in your own codebase with batch tests modelled on `tests/`.
- The About page's "build a producer" path is how a producer gets listed for the community.

## Covers

R-1, R-2, R-3, R-8, R-9, R-10, R-13, R-14, R-15, R-16, R-18, R-24; R-26 through the route's `max_per_source`. The committed scenarios under `scenarios/` are the answer key: `01-ada-export` shows producer and assembler dedupe side by side, `02-cho-refund` the producer's expired rows, `03-memory-leak` scope catching a leak, `04-stale-account-read` stale state, `05-budget-variants` variants used before anything is omitted, and `neg-*` each wrong item's code.

## Files

- `labs/`: the four lab stubs. `solution/`: finished versions, which CI tests.
- `common.py`: the request, the corpus, BM25, Jaccard, the policy, the freeze and the decisions table. `fixed.py`: the two given producers. `impl.py`: the `CWA_W2_IMPL` switch.
- `freeze.py`: run the producers, freeze, assemble, read. `lint.py`: local checks in the assembler's vocabulary. `variants.py`: precompute the variants table.
- `policy/`: the route policy, the profile, the budget and the instructions. `data/variants.json`: the precomputed variants table. The articles, memories and accounts are the Fernway fixtures in `shared/fixtures/`, read through `shared/fernway/`.
- `scenarios.py`, `scenarios/`, `tests/`: the regression check and the answer key.
