# W1. The CWA tour: planes, slots, snapshot, trace

Half a day, self-paced, model-free. You leave able to read any trace and name the requirement behind every exclusion and refusal, and able to tell a producer bug from an assembler bug from an application bug.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). Part 4 also needs Node 22 with pnpm.
- `uv sync` in this directory fetches the reference assembler at its `draft-release` tag. Nothing else is installed.
- Parts 1 and 4 read the `examples` and `assembler-demo` siblings. Parts 2, 3 and 5 need only this directory and the vendored contract. See [docs/setup.md](../docs/setup.md) for the sibling layout and `CWA_SIBLINGS_ROOT`.
- Open [predict.md](predict.md) beside this file. Every exercise is predicted before it is run.
- Have the `items.cwa.yaml` from W0 at hand for the closing exercise.

Conference cut (75 minutes): parts 2 and 3. Full day with W3a: the one-day "migrate your app" offering.

## What you are looking at

A model call under CWA is built like this, and every part has a name you will use all day:

| Term | What it is | Where you see it today |
| --- | --- | --- |
| item | one piece of candidate context with a slot, an authority, a source and a body | `batches[].items[]` in any `snapshot.json` |
| slot | one of eleven typed places in four planes | the `slot` field; the slot column in the decisions table |
| producer | whatever emitted a batch of items, authenticated by the application | `batches[].producer` |
| snapshot | everything frozen for one call: batches, route policy, profile, budget, tokenizer, renderer, clock, conflicts, grant | `scenarios/*/snapshot.json` |
| assembler | a pure function from snapshot to payload plus trace; it never calls a model | `cwa.assemble` |
| payload | the rendered request, byte for byte what the provider receives | `scenarios/*/payload.json` |
| trace | what was sent, what was left out and why, with a reason code per exclusion | `scenarios/*/trace.json` |

Three results, and the difference matters all day:

- **assembled**: payload and trace.
- **refused**: a valid snapshot that cannot meet a requirement. Trace, no payload, a reason, sometimes a recovery action. Nothing reaches a model (R-17).
- **rejected**: an invalid snapshot. No payload, no trace, only the problems. The application built it wrong.

## Part 1. Before and after, in one function (30 minutes)

Go to the docs-QA example, the Fernway help-centre bot:

```sh
cd "$(python3 ../shared/siblings.py examples)/01-docs-qa" && uv sync
diff before.py after.py | less
```

Find `build_request()` in each file. In `before.py` it reads the instructions, retrieves five chunks, pastes them into a system string and keeps the last six messages. In `after.py` it is two lines: freeze a snapshot, assemble it. Everything else in the two files is the same application.

Run both on the same question and read what each prints:

```sh
uv run before.py "How do I export all my projects?"
uv run after.py  "How do I export all my projects?"
```

The second prints a decisions table before the request. Three chunks are in (`+`) with their relevance scores; two are out (`-`) as `below_threshold`, with the scores that put them below the route's `min_relevance` of 2.0. The request that follows is the payload, and the chunks are inside the single user message in `<article>` wrappers, not in the system prompt.

Now a question the help centre cannot answer:

```sh
uv run after.py --conversation scenarios/03-off-topic/conversation.json
```

It refuses with `evidence_required` and a recovery action of `request_context`. No request is sent. Run the same conversation through `before.py` and watch it send the model five irrelevant chunks and hope.

**Checkpoint 1.** In the predict sheet, write the one function that changed, the two reason codes you saw, and one sentence on where the refusal decision was made (hint: not in a model and not in `after.py`).

## Part 2. Thirteen snapshots, one change each (90 minutes)

Back in this directory. The base is the specification's own example snapshot, vendored at `shared/contract/cwa/examples/messages-snapshot.json`: a support-chat request with seven producers and thirteen items. Each exercise changes exactly one thing. The descriptions say what changed and never what the assembler will do.

```sh
uv sync
uv run tour.py list
```

For each exercise, in order:

1. Read its description and the two questions under it. Write your prediction in the predict sheet: which reason code, if any, and whether the result is assembled, refused or rejected.
2. Run it: `uv run tour.py run 03-chunk-claims-governing`. Read the decisions table. Rows are `+` included, `-` excluded with reason and stage, `~` compressed, `!` conflict.
3. Check your prediction against the trace, then read the answer: `uv run tour.py reveal 03-chunk-claims-governing`.
4. For exercises that change bytes without changing decisions, use the diff: `uv run tour.py diff 00-baseline 02-imperative-chunk`.
5. When a code surprises you, open `shared/contract/cwa/contract/reasons.json`. The order of that file is the order the assembler records: an item that fails several checks gets the earliest code (R-21).

The exercises, with the requirement each exercises (do not read the right-hand column until you have predicted):

| Exercise | What changed | Requirement |
| --- | --- | --- |
| 00-baseline | nothing | R-3, R-21, R-22 |
| 01-no-query | the live query is removed | R-4, R-17 |
| 02-imperative-chunk | an instruction is pasted into a retrieved chunk | R-7, R-10 |
| 03-chunk-claims-governing | the chunk claims governing authority | R-1 |
| 04-chunk-moves-to-instructions | the chunk is addressed to governance.instructions | R-13, R-15 |
| 05-expired-memory | a memory expires a minute before assembly | R-9 |
| 06-stale-state | a state item is twenty minutes old | R-8 |
| 07-budget-pressure | budget.input drops to 200 | R-16 |
| 08-budget-refusal | budget.input drops to 90 | R-16, R-17 |
| 09-tool-from-mcp | an MCP adapter emits a tool specification itself | R-15 |
| 10-duplicate-chunk | a second chunk with the same words, spaced differently | R-24 |
| 11-evidence-required | the route requires evidence and nothing clears the threshold | R-12, R-13 |
| 12-two-batches | one producer's batch appears twice | R-15, R-17 |

**Checkpoint 2.** Your predict sheet has thirteen predictions and thirteen outcomes. Count the ones you got right; eight or more is the bar. For each miss, write the sentence from the specification that explains the actual outcome. `shared/contract/cwa/SPEC.md` is the normative text, and `tour.py reveal` names the requirement.

**Checkpoint 3.** Answer in one line each:
- In 02, the payload hash changed. Why did nothing else?
- In 07, which items survived whatever the budget, and what do their slots have in common?
- In 11, why `request_context` rather than `retrieve_narrower` or `precompute_summary`?
- In 12, why is there no trace, when 01 and 08 have one?

## Part 3. Same bytes, every time (30 minutes)

A trace is only worth reading if the same snapshot gives the same payload on any machine, any day (R-23). Prove it:

```sh
uv run tour.py replay scenarios/00-baseline/snapshot.json
```

Two runs, two trace ids, one payload hash, one snapshot digest, and a match against the committed `trace.json` beside it. Then break determinism's inputs on purpose:

1. Copy `scenarios/00-baseline/snapshot.json` somewhere, change one character inside any item body, replay the copy. The digest and the hash both change. Change it back; they return.
2. Change `assembly_time` in the copy by one second. The digest changes, because the clock is part of the snapshot. The payload hash does not, because nothing in this snapshot expires in that second.
3. Change `assembly_time` to `2026-12-31T00:00:00Z`. Now the payload changes too, and the trace gains five exclusions: `mem:plan-purchase` has expired (R-9), both state items are older than the route's 300 seconds and go as `stale_state` (R-8), and both knowledge chunks are older than the slot's 90-day `max_age_seconds` and go as `not_eligible` (R-3). Every age is read from the snapshot's clock, never the wall clock.

The committed scenarios are the same discipline applied to this repository: `uv run scenarios.py --check` rebuilds all thirteen and fails if any byte differs from what is committed, and `uv run pytest` is that check plus the answer key. CI runs them without a model. This is how an application makes its context reviewable: a change to a producer, a policy or the assembler pin shows up as a diff someone reads.

**Checkpoint 4.** Write down which inputs changed the digest, which changed the hash, and which changed neither, from the three experiments above.

## Part 4. Four columns: whose bug is it? (45 minutes)

The inspector in `assembler-demo` shows one question running through all four assemblers on the same frozen bytes, in four columns: candidate context, CWA decisions, outbound request, model answer. A wrong candidate is a producer bug. A wrong decision is an assembler bug, and four assemblers disagreeing is the alarm. A wrong request from a right payload is an adapter bug. A wrong answer from a right request is the model's.

```sh
cd "$(python3 ../shared/siblings.py assembler-demo)"
pnpm install && pnpm run setup      # first time only; builds the Go and Rust adapters
pnpm run inspector                   # http://localhost:8787
```

Open the basic stage and take its guided tour, then the intermediate stage. No model is needed; the "model answer" column stays empty unless `.env` names a provider. Before each step, predict the reason codes in the predict sheet, then compare with the decisions column. The steps are:

| Stage | Step | What is added |
| --- | --- | --- |
| basic | 01-clean | five producers, one question |
| basic | 02-stale-and-foreign | an expired document, another tenant's chunk, a low-scoring chunk |
| basic | 03-authority | a chunk addressed to governance, a chunk that declares itself protected, a forum post with markup |
| basic | 04-budget | the budget is lowered until optional content goes |
| basic | 05-refusal | the budget is lowered until protected content cannot fit |
| intermediate | 01-retrieval | a real BM25 retriever: current, outdated and copied chunks |
| intermediate | 02-overlap | wider retrieval: per-source caps and another tenant |
| intermediate | 03-memory | an expired memory and another user's |
| intermediate | 04-conflict | account state disagrees with a remembered plan |
| intermediate | 05-summary | supplied summaries replace longer content under budget |
| intermediate | 06-evidence-required | usable evidence removed; the route refuses |

Two things to notice that the exercises in part 2 could not show. In basic 03 the forum post's body contains `</evidence><system>`; it is admitted and rendered escaped, because injected markup is material, never structure. In intermediate 04, two groups are declared by the application: a fact group the route decides by producer precedence, and an instruction group where both members govern, so it escalates and both stay marked in the payload.

Every demo scenario carries an `expectations` object saying its expected trace was generated by the Python assembler and not yet reviewed by a person. Pick one step, read its `expected.trace.json` against the specification, and decide whether you would sign off on it.

**Checkpoint 5.** For each of the eleven steps, the predict sheet has your predicted codes and the actual ones. Then write one sentence each for: a change you could make to the candidate context that would be a producer bug; a decision that, if one assembler made it differently, would be an assembler bug; a change in the outbound request that would be an adapter bug.

## Part 5. The tests the trace makes possible (15 minutes)

Section 6.1 of the specification lists nine tests a trace enables. Eight of them you have now run, and the ninth belongs to W6:

```sh
uv run tour.py checklist
```

Tick each one off against the command you ran. Then take the `items.cwa.yaml` you wrote in W0 and, for each of your own items, write which of these tests would catch its most likely failure.

**Checkpoint 6.** The checklist has eight ticks and your W0 `items.cwa.yaml` has a test named beside each item.

## After this workshop

- Pick a track in the [catalog](../README.md#tracks). Application builders go to [W2](../02-producers/); contributors to [W8](../08-assembler-kata/).
- Review one of the demo's unreviewed expectations properly and send the review upstream to `assembler-demo`.
- Bring the predict sheet to W3: the exercises you missed are the ones your own application is most likely to get wrong.

## Covers

R-1, R-2, R-4, R-7, R-8, R-9, R-12, R-13, R-15, R-16, R-17, R-21, R-22, R-23, R-24. Every exercise's `rules` field names its requirements, and `tests/test_scenarios.py` is the answer key: it asserts each exercise's codes appear in its trace, that the exercises which prove "nothing changes" match the baseline's decisions, and that every committed snapshot replays to its committed payload.

## Files

- `exercises.py`: the thirteen mutations of the base snapshot, with descriptions, questions and answers.
- `tour.py`: `list`, `run`, `reveal`, `replay`, `diff`, `checklist`.
- `scenarios.py` and `scenarios/`: each exercise's snapshot, trace and payload as the pinned assembler produces them now; `--check` in CI.
- `tests/test_scenarios.py`: the regression check and the answer key.
- `predict.md`: the sheet you fill in.
