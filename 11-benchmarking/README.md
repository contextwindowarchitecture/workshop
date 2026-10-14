# W11. Benchmarking CWA: does it help, and what does the number mean

Half a day. For evaluation engineers and the leads deciding whether to adopt. Model-free throughout: every number here is read from runs the sibling repositories committed, and the one thing this module computes itself needs no model either. Lab A runs here alone; Labs B and C read the `examples` and `benchmark` siblings ([docs/setup.md](../docs/setup.md), `CWA_SIBLINGS_ROOT`, and `CWA_SIBLING_BENCHMARK` when the benchmark is checked out elsewhere).

CWA makes a claim that can be tested in two halves. The first half is about the assembler and needs no model: the same snapshot gives the same bytes (R-23), the request sent is the payload (R-5), a refusal sends nothing (R-17). The second half is about what a model does with context assembled that way, and every number in it is a statistical estimate about one model on one task. The discipline this module teaches is to keep the halves apart, and to say of every number which half it belongs to.

## What you leave with

- The invariants run over every snapshot this repository commits, which is the model-free half of any CWA benchmark.
- A committed fourteen-model run of the examples gallery read from its files: invariants first, then the measures that depend on the model, with the range across repeats beside the average.
- A committed Domain 2 run of the viability benchmark read from its files: eleven ways of building the same conversation's context and two uncapped controls, side by side, with the column that tells a payload failure from a model failure.
- One construct of your own, written as an expectation the gallery could grade.

## Part 1. Two families, three kinds of result (30 minutes)

| Family | What it holds constant | What varies | Where |
| --- | --- | --- | --- |
| The examples gallery | one application (Fernway), its committed scenarios, the assembler at its pin | fourteen models on OpenRouter, ten repeats | `examples/gallery` |
| The viability benchmark, Domain 1 | the specification at its pin | four assemblers, treated as black boxes through the adapter protocol | `benchmark/domain1` |
| The viability benchmark, Domain 2 | one model, its settings, the facts, the user's turns, the budget, the counter, the grader | the way the payload is built: eleven arms, from "concatenate everything" to the CWA pipeline, and two uncapped controls | `benchmark/domain2` |

The gallery calls itself a showcase, not a benchmark: three to six cases per example is a smoke test, the checks are patterns, and it ranks no model. It still separates three kinds of result, and the distinction carries to any benchmark of a context architecture:

| Kind | Holds for | A failure means |
| --- | --- | --- |
| Invariants: payload sent as rendered, refusal sends nothing, every snapshot replays, same question gives the same snapshot | every model | a bug in the application or the assembler. Never a finding about a model. |
| Construct measures: grounding, conflict adherence, exclusion respect, resistance to injected text, allowed actions | one model at a time | how that model used the context it was given |
| The application's own eval suite | one model, graded by the application's gate | what W7's gate would have said |

[meaning.py](https://github.com/contextwindowarchitecture/examples/blob/main/gallery/meaning.py) in the gallery writes, for every page of numbers, what it says about CWA, and for every number, the one thing it is evidence of, or plainly that it is the model's or the host's doing. Read it before any table.

**Checkpoint 1.** Which kind of result is a `payload_sent` failure, and what you would do about it. Which kind is a model citing an article it was not sent.

## Part 2. Lab A: the invariants, over this repository (30 minutes)

```sh
uv sync
uv run invariants.py          # every committed snapshot in W1 to W7, W9, W10 and the capstones
uv run pytest
```

[invariants.py](invariants.py) walks the repository for every committed snapshot, wherever its module keeps it: a `snapshot.json` beside a trace, a run record with `inferences`, an eval recording with `attempts`. For each it assembles twice and compares (R-23), validates the trace against the published schema (R-21), and, where a trace was committed beside it, compares the fresh trace with the recorded one. A snapshot committed with a `rejected.json` is expected to be rejected with the recorded problems: W1's two-batches exercise is one, and a rejection is an invariant too (R-5).

One hundred and sixty-four snapshots at the time of writing, none failing. Break one on purpose: edit a committed trace in W2's scenarios and run again, then `git checkout` it. Then read the per-module table and notice which modules commit traces beside their snapshots and which commit only the snapshot: the `recorded` column counts only the first kind.

**Checkpoint 2.** The snapshot count, the one expected rejection, and the module whose snapshots have no recorded trace to compare with.

## Part 3. Lab B: a fourteen-model run, from its files (60 minutes)

```sh
export CWA_SIBLINGS_ROOT=..               # wherever the siblings are
uv run bench_read.py                      # the newest graded run under examples/gallery/results
uv run bench_read.py --measure grounding  # one measure by model, with the lowest and highest repeat
uv run bench_read.py --measure evals
```

The committed run of 2026-10-05 has fourteen models, 2,380 jobs, and spent $9.44 of a $30 cap. Its invariants pass 5,460 of 5,460: the same context went to every model in 01 to 03, every request carried the rendered payload, every snapshot replayed. That line comes first because nothing after it means anything if it does not hold.

Then the measures. Read the table across before down. `conflict`, `excluded` and `refusal` are at or near their ceiling for every model: the cases show the construct at work and are too gentle to rank capable models, which the gallery's README says of itself. `claims` (does the agent say it enabled the webhook exactly when it did) and `evals` (05's own gate) are where the models spread. `--measure grounding` shows the second thing a single number hides: the average and the range across ten repeats. Several models average 0.996 with a worst repeat of 0.958; a suite run once reports whichever repeat it got.

What is CWA's in this table and what is not. The invariants are CWA's. That 01 to 03 gave every model the same snapshot is CWA's (R-23). Grounding can be measured at all because every article has an id and user content is marked, never elevated (R-10, R-13): that is CWA's. Which model cites better, reasons longer or costs more is the model's and the host's, and the gallery's tokens and cost pages say so number by number: the assembler's count is right by its own tokenizer, and a model's own count can be several times it, which is what `margin_percent` (R-16) exists to cover and what a run like this measures after the fact.

With the examples' environments synced, two more commands in `examples/gallery` are worth running: `uv run grade.py results/<run-id>` regrades a run from its files, with no model, after the expectations change; `uv run serve.py` serves the viewer, the showcase, which sets two models side by side and keeps the same numbers by construct under the hood. Neither sends anything.

**Checkpoint 3.** The invariants line. The two measures where the models spread. One model's grounding average and its worst repeat, and what a gate that runs its suite once would have seen.

## Part 4. Lab C: eleven ways to build the same context (60 minutes)

```sh
export CWA_SIBLING_BENCHMARK=../cwa-extended/benchmark   # when the benchmark is not under the root
uv run domain2_read.py                                   # the latest committed Domain 2 run, S2 by arm
```

Domain 2 asks one question: over a long conversation, does a model given CWA-assembled context keep doing the task where a model given conventionally assembled context degrades, with everything else held equal? The model, its settings, the facts, the user's turns, the budget, the token counter and the grader are the same in every arm. Only the way the payload is built changes:

| Arm | Builds |
| --- | --- |
| `control-full`, `control-concat` | the whole conversation with no budget: upper bounds |
| `concat` | every turn as chat; when that exceeds the budget, nothing is sent |
| `truncate`, `truncate-pinned` | the newest turns that fit, the system prompt dropped or pinned. `truncate-pinned` is the fair reference |
| `window` | the last ten turns |
| `summary` | the last ten turns and a rolling summary the model writes: the strongest conventional control |
| `cwa-history` | CWA's format with history only |
| `cwa-state` | plus `state.task` written from the facts the user stated: the upper bound for state |
| `cwa-state-x` | plus `state.task` written by the model, turn by turn: the realistic arm |
| `cwa-memory`, `cwa-pipeline` | `cwa-state` with recent turns as history and older facts as memory; the second adds supersession and deduplication |
| `cwa-format` | `window`'s exact selection, rendered as CWA renders it: the format control |

The reader prints, for each arm and budget, the share of probes answered right, the 95% interval from a bootstrap over conversations, and the share of probes whose needed fact was in the payload at all. The last column is the one to learn: a wrong answer with the fact absent is the payload's failure, and with the fact present it is the model's.

The committed run is a pilot-size replay (`size = pilot`, every call a cache hit, so no model ran), and its intervals are wide. The published result, from the recorded sizes at 8,192 tokens, is in the benchmark's [docs/domain2.md](https://github.com/contextwindowarchitecture/benchmark/blob/main/docs/domain2.md):

| Arm | Aptitude | vs `truncate-pinned` | Fact in payload |
| --- | --- | --- | --- |
| `concat` | 0.633 | −0.190 | 69% |
| `truncate-pinned` | 0.824 | | 90% |
| `summary` | 0.855 | +0.032 | 93% |
| `cwa-history` | 0.799 | −0.025 | 86% |
| `cwa-state-x` | 0.833 | +0.009 [−0.025, +0.040] | 94% |
| `cwa-state` | 0.972 | +0.148 | 100% |
| `cwa-memory`, `cwa-pipeline` | 0.989 | +0.166 | 100% |

Read the two tables together and the finding is the same in both. The gain comes from the state the application writes from what the user said, which CWA gives a protected place every budget keeps. Model-written state is level with pinned truncation: its interval straddles zero. History alone in CWA's format gains nothing. The assembler was exact throughout: 220,608 assemblies on four assemblers, every one equal to the prediction and clean under Domain 1's audit, which is the invariant half holding while the model half is measured.

Domain 1 is the invariant half at scale, with no model anywhere: 65 cases and 25 rejections on all four assemblers, 4,900 of 4,900 decisions identical on the host, across fourteen environment cells and on seven platform variants, 10,000 fuzzed snapshots agreeing, and a trace auditor that never assembles yet catches 1,616 of 1,626 deliberately broken traces. The five defects it found during development were fixed upstream, and the specification adopted four new conformance cases from them and changed a fifth, which is W10's subject. Running either domain yourself means `uv sync` at the benchmark root and `uv run cwabench setup` to build the four adapters, which needs the Go, Rust and Node toolchains; the committed runs are why this module does not.

**Checkpoint 4.** The fair baseline and why. The gap between `cwa-state` and `truncate-pinned` in the pilot and in the published run. Whether `cwa-state-x` beats the baseline, and how you know. What `truncate-pinned`'s fact-in-payload share says about where its errors come from.

## Part 5. Lab D: one construct of your own (45 minutes)

A construct is a CWA decision a case exercises, and an expectation is how a grader with no model tells whether the model respected it. The gallery's [expectations.toml](https://github.com/contextwindowarchitecture/examples/blob/main/gallery/expectations.toml) writes each as a table keyed by case, with a comment naming the decision: `answer.mentions_any`, `grounding.must_cite`, `conflict.winner` and `conflict.loser`, `excluded.mentions_none`, `untrusted.must_not_attempt`, `actions.must_call` and `must_not_call`.

[expectations.example.toml](expectations.example.toml) writes two for scenarios this repository commits, in the gallery's format. Write a third for a scenario from your own module, or from the capstone you built. The questions to answer before the phrases:

1. Which decision in the trace does the case exercise? Name the row: a `below_threshold` exclusion, a `conflict_lost`, a `superseded_by`, a compressed variant.
2. What would an answer look like if the model ignored that decision? That is the phrase for `mentions_none` or `loser`.
3. What would it look like if the model respected it? That is `must_cite`, `winner` or `mentions_any`.
4. What phrasing would the pattern miss? Write it down beside the expectation; the gallery's checks are patterns and say so.

**Checkpoint 5.** Your construct, its trace row, its expectation, and the phrasing it would miss.

## What is here

```
invariants.py              every committed snapshot in the repository: replay, schema, recorded trace, expected rejection
bench_read.py              a committed examples-gallery run from summary.json: invariants, measures by model, range across repeats
domain2_read.py            a committed Domain 2 run from suites/S2/summary.json: arms, intervals, fact in payload
expectations.example.toml  two constructs written as expectations the gallery could grade
tests/                     the invariants over the repository, and the readers' arithmetic
```

Facilitator run sheet: [docs/facilitator/11-benchmarking.md](../docs/facilitator/11-benchmarking.md). Worksheet: [WORKSHEET.md](WORKSHEET.md).
