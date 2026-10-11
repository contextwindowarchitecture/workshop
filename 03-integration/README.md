# W3a. Integrating CWA into an existing application

A full day, self-paced, model-free. You leave with an application you migrated yourself: every model call frozen into a snapshot, decided by the assembler, explained by a trace, handed to the provider unchanged, and checked by guards that do not care how the model was asked. You also leave with a written list of which of the application's conformance duties it now meets.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` installs the reference assembler and the OpenAI SDK. No model is needed; with `OPENAI_BASE_URL` set, both apps send for real.
- W1 and W2. W9 module A helps: the producers you wrote there are the ones this application needs.
- Open [MIGRATION.md](MIGRATION.md), the six steps you follow, and [inventory.md](inventory.md), the worksheet.

In another language, the same migration uses that language's port under the names in [docs/assemblers.md](../docs/assemblers.md); the seams and the guards do not move. This is W3a. W3b, the framework seams, is the [seams/](seams/) module in this directory: it builds on this application and proves, with recording models, that each framework hands the model exactly the payload. One-day offering: W1 in the morning, W3a in the afternoon; W3b is the half day after.

## The application

`before/app.py` is the Fernway account assistant as teams usually write it. One function pastes the instructions, the account line, every memory on file, the five best-scoring help-centre paragraphs and the last six messages into one request and sends it. Read [before/README.md](before/README.md) with W0's seven failure modes beside you; the table there says where each one lives in the code.

`after/` is your copy. It starts identical, plus stubs for the files you will write: `producers.py`, `context.py`, `guards.py` and a `policy/` folder. `solution/` is the finished migration, a reference to read when stuck.

```sh
uv sync
uv run python -m before.app --conversation scenarios/02-ben-plan-conflict/conversation.json
uv run python -m solution.app --conversation scenarios/02-ben-plan-conflict/conversation.json
```

The before app prints a system string in which "Workspace Kitewood Studio is on the Business plan" and "Their workspace is on the Team plan" sit a few lines apart with equal standing. The migrated app prints a decisions table in which the memory is excluded as `conflict_lost` by a declared fact group, decided by the route's producer precedence, and the account is protected.

## The application's duties

The specification's §1 names the MUSTs no component can meet on the application's behalf. They are the migration's acceptance criteria, and the inventory's last table:

| Duty | Requirement | Where it lands in `after/` |
| --- | --- | --- |
| enforce invariants outside the model | R-5 | `guards.py`, wired into `answer()` |
| write state itself, never from model output | R-8 | `producers.accounts_db`, freshness = read time |
| declare conflict groups | R-11 | `context.conflict_groups` from the producers' facts |
| authenticate each producer and bind identity outside the items | R-15 | the route policy's `producers`, stamped at freeze |
| make every external read before freezing; refreeze for any retry | R-12, R-23 | `context.snapshot` runs every producer, then freezes once |
| set `parser: true` where a downstream parser exists | R-4 | not on this route; note it in the inventory |
| set `budget.input` from the model's context limit less `reserved_output` | R-16 | `context.budget()` from `policy/assembly.json` |
| version profiles and deploy only evaluated ones | R-19, R-20 | `policy/profile.json`, `version: 1`, unevaluated for now |
| hand the payload over unchanged, with no text of its own | §1 | `provider.request_for` |

## The six steps

[MIGRATION.md](MIGRATION.md) walks them with the tests that go green at each one. In brief:

1. **Name the slots you already send.** Inventory the old prompt into slots and authorities, and list the "never" sentences. No code changes. (30 minutes)
2. **Freeze a snapshot and hand it to an assembler.** `context.snapshot()` and `assemble()`; `build_request()` becomes two lines. The first snapshot is rejected, and the problems the assembler lists are the to-do list. (60 minutes)
3. **Give every item an authority and a source.** Five producers, two of which also return the facts their items assert, and `conflict_groups()`. Scope keys on everything that has them. (90 minutes)
4. **Check the trace.** Read the table for the five conversations. Replay a snapshot and compare the hash. Remove a field and watch the exclusion. (30 minutes)
5. **Pick a placement profile and set the budget.** The route policy, the profile with its version, the budget computed from the model's limit. (60 minutes)
6. **Move enforcement out of the prompt.** Two guards on the reply; the sentences stay in the instructions as guidance. (45 minutes)

```sh
CWA_W3_IMPL=after uv run pytest          # your migration, step by step
uv run pytest                            # the solution, and the before app's failure modes asserted
```

## What the five conversations show

| Scenario | Before | After |
| --- | --- | --- |
| `01-ada-export` | everything pasted, revoked and expired memories included | two producer-reported rows, the exact FAQ copy excluded, a replayable digest |
| `02-ben-plan-conflict` | "Business plan" and "Team plan" with equal standing | `fact:plan` decided by policy, the memory `conflict_lost`, the account protected |
| `03-off-topic` | five irrelevant paragraphs sent anyway | refused `evidence_required`, recovery `request_context`, nothing sent |
| `04-long-conversation` | the last six messages whatever their size | the oldest turns `over_budget` under the history cap, the query never dropped |
| `05-memory-leak` | a producer bug ships another user's memories | each leaked memory `out_of_scope`, the leak visible by producer |

## Checkpoints

1. The inventory's first two tables are filled.
2. `test_build_request_freezes_and_assembles` and `test_the_same_snapshot_renders_the_same_bytes` pass against `after/`.
3. The four step-3 tests pass. You can say, without looking, which producer reports `revoked` and why the assembler and not the producer records `conflict_lost`.
4. The inventory's step-4 lines are filled from your own run, not from the solution's scenarios.
5. The four step-5 tests pass. You can defend every number in `after/policy/`.
6. Both guard tests pass, and `after/app.py`'s `answer()` withholds a reply that quotes an unverified price.
7. The inventory's last table is filled, with `parser: true` honestly marked not applicable and profile evaluation honestly marked open.

## After this workshop

- Run step 1 on one production prompt you own, and file the slot map where your team keeps design docs.
- W4 adds variants, two routes and escalation to this application. W5 adds tools. W6 evaluates the profile you left unevaluated.
- If a route you need cannot be expressed in a route policy, that is a spec-change issue; the About page says how.

## Covers

R-2, R-4, R-5, R-7, R-8, R-9, R-11, R-12, R-13, R-15, R-16, R-17, R-19, R-20, R-21, R-23, R-24; §1's application conformance claim throughout.

## Files

- `before/`: the legacy app, frozen; `tests/test_before.py` asserts its failure modes.
- `after/`: your copy with stubs. `solution/`: the finished migration, which CI tests. `impl.py`: the `CWA_W3_IMPL` switch.
- `request.py`: the request both apps answer. `provider.py`: the OpenAI-compatible last mile, pure `request_for()` plus `send()`.
- `MIGRATION.md`, `inventory.md`: the steps and the worksheet.
- `scenarios.py`, `scenarios/`, `tests/`: five conversations, their committed snapshots, traces and payloads, and the step-by-step tests.
