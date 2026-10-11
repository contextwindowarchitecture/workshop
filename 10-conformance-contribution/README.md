# W10. Conformance and contributing to the specification

Half a day. For anyone who has finished W2 or W8 and wants to change the specification: a case it should have, a rule it should say more plainly, an implementation it should list. Model-free. Lab A runs here alone; Lab B needs the `contextwindowarchitecture` sibling checked out (`CWA_SIBLINGS_ROOT`, [docs/setup.md](../docs/setup.md)).

The specification is data with prose written from it. `contract/requirements.json` holds the requirements, `contract/reasons.json` the reason codes in the precedence R-21 applies, `contract/slot-defaults.json` the policy defaults R-3 fills, and `conformance/cases/` the cases every listed assembler must pass. The blocks between `generated` markers in `SPEC.md` and the guides are written from those files by `conformance/check.py --write`. So a change to the specification is a change to data, and a case is how you prove the data means what you say.

## What you leave with

- A conformance case written the way the specification's generators write theirs, from a table of intended outcomes, that the reference assembler passes and a plausible wrong assembler fails.
- The specification's own checker run over your case, which is what CI runs over a pull request.
- A pull request description for the case and a draft spec-change proposal in the project's own issue template, each written against the three questions a maintainer asks.

## Part 1. The anatomy of a case (30 minutes)

Open [shared/contract/cwa/conformance/cases/conflict-fact/](../shared/contract/cwa/conformance/cases/conflict-fact/), the vendored copy of a published case.

| File | What it holds | Who reads it |
| --- | --- | --- |
| `case.json` | `id`, the requirement ids it exercises (`rules`), one sentence of `description` | people, and `check.py` for the id |
| `snapshot.json` | the frozen input, valid against `snapshot.schema.json` | the assembler under test |
| `expected.trace.json` | the trace a conformant assembler emits, `trace_id` and `timings` aside | the runner, field by field |
| `expected.payload.txt` | the rendered bytes, compared byte for byte | the runner; absent when the case expects a refusal (R-17) |

A rejection under `conformance/rejections/` has only `case.json` and `snapshot.json`: it breaks exactly one snapshot check, and a conformant assembler rejects it before assembly, so there is nothing to expect.

The cases that matter most have generators. Open [conformance/generators/conflicts.py](https://github.com/contextwindowarchitecture/contextwindowarchitecture/blob/main/conformance/generators/conflicts.py) in the specification repository (the generators are not vendored; the sibling checkout has them under `conformance/generators/`). Each case is a table: candidates with their producer, groups with the decision each intends (`decided_by`, `resolution`, `winner`, the members excluded). The expected trace and payload are derived from that table. They are never produced by running an assembler, because a case produced that way cannot fail the assembler that produced it. The generator checks only that the table is self-consistent with the rules in [conformance/README.md](../shared/contract/cwa/conformance/README.md).

**Checkpoint 1.** In `conflict-fact`, find the group `f-tie`. What decides it, and what would have to differ for the clock to decide it instead? Which file does a refusal case not have, and which requirement says why?

## Part 2. Lab A: a case the corpus lacks (90 minutes)

W8's kata left one defect in [08-assembler-kata/defects/uncovered.json](../08-assembler-kata/defects/uncovered.json): an assembler that applies a freshness tie-break whether or not the fact policy permits one passes every published case. R-11 is plain that "a freshness tie-break, when the policy sets one, decides only among several leaders". The corpus has a group with two leaders and the permission (`f-freshness`), and a group with two leaders at the same instant and no permission (`f-tie`), where the clock cannot decide anyway. It has no group with two leaders at different instants and no permission. That is the case to write.

```sh
uv sync
uv run generate.py          # the table in generate.py -> cases/conflict-tiebreak-not-permitted/
uv run verify.py            # the reference passes; a copy with the uncovered defect fails
uv run pytest
```

[generate.py](generate.py) is built the way the spec's generators are. `TABLE` names the candidates with their producers, one fact group with two leaders from the top-ranked producer at different instants, a fact policy with `precedence` but no `freshness_tiebreak`, and `on_unresolved: refuse`. It intends `decided_by: escalated`, `resolution: refused`, refusal `conflict_unresolved`. `expected_trace()` is written from that table, field by field, in the order R-21 lists them. The only computed value is `context.snapshot_digest`, which is a published function (SHA-256 over the RFC 8785 serialization of the normalized snapshot) that the generators ship in `digest.py`, and the workshop imports it from the sibling when it is checked out.

[verify.py](verify.py) is the proof a case needs. It runs the reference assembler, which must pass, then copies the installed assembler to a scratch package, applies the uncovered defect's one-line change, and runs that, which must fail. The first differing field is printed. With the defect, the group is `decided_by: freshness`, `kb:window-1` is excluded `conflict_lost`, and assembly goes ahead with 33 tokens where the case expects a refusal.

Now change the table and watch the derivation hold:

1. Set `freshness_tiebreak: True` on the policy. Regenerate. The expected trace now has to intend a different outcome, and `generate.py` will not know which: that is the point. Work out the new row (`decided_by: freshness`, `winner: kb:window-2`, `kb:window-1` excluded `conflict_lost`, `result` no longer null) and see how much of the trace changes. Then put the table back.
2. Give both leaders the same instant. Regenerate and run `verify.py`. The broken assembler now passes: the case no longer isolates the defect. Put it back.
3. Change `on_unresolved` to `surface`. What does the case become, and does it still catch the defect?

**Checkpoint 2.** The field where the broken assembler first differs, and why `f-tie` in the published corpus never caught it.

## Part 3. Lab B: the specification's own checker (45 minutes)

A pull request that adds a case has to pass `conformance/check.py`: every case against the schemas, its digest against the definition, a refusal with no payload file, reason codes against the requirements, and the listed implementations' stored reports against the corpus as it now stands.

```sh
export CWA_SIBLINGS_ROOT=..   # wherever the siblings are checked out
uv run spec_check.py          # copies the spec sibling to scratch, adds the case, runs check.py
uv run spec_check.py --keep   # keep the copy to branch from
```

The sibling checkout is never modified. The checker reports the corpus count with your case in it and `ok`, or lists each problem. Try breaking the case on purpose: edit the digest in the scratch copy's `expected.trace.json` and run `python3 conformance/check.py` there. Then put a stray `expected.payload.txt` beside the refusal and run it again.

Where the case really goes. The workshop's `generate.py` is a teaching copy. In the specification the table joins `conformance/generators/conflicts.py`, because that generator already owns the fact-group rules and `all.py` regenerates it with the rest. The pull request carries the generator change, the regenerated files, and a bullet in `CHANGES.md` under the newest revision.

**Checkpoint 3.** What `check.py` printed with your case added, and which of its checks would have caught each of the two breakages you tried.

## Part 4. Lab C: writing to the project (45 minutes)

The project takes three kinds of issue, each with a template in `.github/ISSUE_TEMPLATE/`:

| Template | For | Asks for |
| --- | --- | --- |
| A problem with a conformance case | a case whose expectation looks wrong, or that two implementations read differently | the case; what it expects and what it should, citing the rule that decides |
| A change to the specification | SPEC.md, a schema, the contract data or conformance/README.md | what should change, naming R-n or the section and what it says now; why, with a snapshot or trace that shows it |
| An implementation to list | help listing an assembler | the repository; what you need |

Questions go to Discussions. A change to what a requirement means is agreed in an issue before a diff. A pull request needs the checks green, derived text regenerated rather than edited, cases regenerated from their generators, a `CHANGES.md` bullet when a rule changes, and a `Signed-off-by` line on every commit (`git commit -s`). Maintainers squash-merge.

Two drafts to write, in [drafts/](drafts/):

- [case-addition.md](drafts/case-addition.md): the pull request description for the case from Lab A. A worked draft is there; make it yours or tighten it. The maintainer's three questions: what gap does it close, what does it say about the rule as written, what did every listed assembler do with it.
- [spec-change.md](drafts/spec-change.md): a change proposal in the spec-change template. The worked example proposes allowing an object for a profile's `evaluation.result`, which W4 and W6 found cannot hold a suite's result without flattening it to a string. It is written to be argued with, and the last section argues with it. Then write your own, for something a module of this repository made you want to change.

When the drafts are ready, `uv run upstream.py --into <your fork of the specification>` copies the case into that checkout's `conformance/cases/` and prints the remaining steps: the checker, the generator move, the `CHANGES.md` bullet, the listed assemblers, the signed commit. It never touches git.

**Checkpoint 4.** The two drafts, and the thing from this repository you would propose first.

## What is here

```
generate.py       the table and the derivation: writes cases/conflict-tiebreak-not-permitted/
verify.py         the reference passes, the uncovered defect fails, first difference printed
spec_check.py     the spec sibling copied to scratch with the case added, conformance/check.py run over it
upstream.py       the case copied into a specification checkout of yours, with the pull request's remaining steps printed
cases/            the generated case: case.json, snapshot.json, expected.trace.json (no payload: a refusal)
drafts/           the pull request description and the spec-change proposal
tests/            the committed case is current, valid, passed by the reference, failed by the defect, and not covered by the corpus
```

Facilitator run sheet: [docs/facilitator/10-conformance-contribution.md](../docs/facilitator/10-conformance-contribution.md). Worksheet: [WORKSHEET.md](WORKSHEET.md).
