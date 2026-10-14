# W10. Conformance and contributing to the specification

Half a day. For anyone who has finished W2 or W8 and wants to change the specification: a case it should have, a rule it should say more plainly, an implementation it should list. Model-free. Labs A and B run here alone; Lab B's checker needs the `contextwindowarchitecture` sibling checked out (`CWA_SIBLINGS_ROOT`, [docs/setup.md](../docs/setup.md)).

The specification is data with prose written from it. `contract/requirements.json` holds the requirements, `contract/reasons.json` the reason codes in the precedence R-21 applies, `contract/slot-defaults.json` the policy defaults R-3 fills, and `conformance/cases/` the cases every listed assembler must pass. The blocks between `generated` markers in `SPEC.md` and the guides are written from those files by `conformance/check.py --write`. So a change to the specification is a change to data, and a case is how you prove the data means what you say.

The exercise does not depend on the corpus having a gap. W8's kata ships eleven one-line defects in the reference assembler; you pick one, write the case that isolates it from a table of intended outcomes, and prove it: the reference passes, the defective copy fails, the other ten defects mostly do not trip it. Whether the published corpus already catches your defect is the last question, not the first, and a published case to compare yours with makes the exercise better, not worse.

## What you leave with

- A conformance case written the way the specification's generators write theirs, from a table of intended outcomes, that the reference assembler passes and the defect you chose fails.
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

## Part 2. The worked example (30 minutes)

```sh
uv sync
uv run generate.py                 # the table in generate.py -> cases/conflict-tiebreak-not-permitted/
uv run verify.py                   # the reference passes; a copy with its defect fails
uv run verify.py --all-defects     # which of W8's eleven defects this case catches
uv run pytest
```

[generate.py](generate.py) is built the way the spec's generators are. `TABLE` names the candidates with their producers, one fact group with two leaders from the top-ranked producer at different instants, a fact policy with `precedence` but no `freshness_tiebreak`, and `on_unresolved: refuse`. It intends `decided_by: escalated`, `resolution: refused`, refusal `conflict_unresolved`. `expected_trace()` is written from that table, field by field, in the order R-21 lists them. The only computed value is `context.snapshot_digest`, a published function (SHA-256 over the RFC 8785 serialization of the normalized snapshot) that the generators ship in `digest.py`; the workshop imports it from the sibling when it is checked out.

[verify.py](verify.py) is the proof a case needs. It runs the reference assembler, which must pass. Then it copies the installed assembler to a scratch package, applies one of W8's defects, and runs that. For this case's defect, `tiebreak-without-permission`, the copy resolves the group `decided_by: freshness`, excludes `kb:window-1` with `conflict_lost`, and assembles 33 tokens where the case expects a refusal; the first differing field is `/conflicts/0/decided_by`. `--all-defects` runs all eleven: this case catches one. That is the second thing a case must be: specific. A case every defect trips is testing nothing in particular.

When this module was written the published corpus had no group with two leaders at different instants and no permission, so this defect passed every published case and W8 lists it in `uncovered.json`. If the corpus has since gained such a case, the example still works exactly as above, and Part 4 tells you what to do with the fact.

**Checkpoint 2.** The field where the defective assembler first differs, and how many of the eleven defects the example catches.

## Part 3. Lab A: your case (75 minutes)

Pick a defect from [08-assembler-kata/defects/manifest.json](../08-assembler-kata/defects/manifest.json) (ten, each with the rule it breaks, the line it changes and the published cases that catch it) or `uncovered.json`. Read the rule it breaks in the vendored `conformance/README.md`. Then:

```sh
cp template.py my_case.py          # generate.py with the table emptied; set DEFAULT_ID to an id of your own
uv run my_case.py                  # -> cases/<your id>/
uv run verify.py --case <your id> --defect <the defect>
uv run verify.py --case <your id> --all-defects
```

The derivation in the template is the worked example's: one fact group, a refusal, and no `expected.payload.txt`. It serves a conflict defect as it stands. For any other defect, change `snapshot()` and `expected_trace()` to say what your table intends, and when your case assembles, have `files()` write the expected payload too, derived from the table like the trace.

Three things must hold. The reference passes: your table says what the rules say. Your defect fails: the case reaches the line the defect changes. Most other defects do not trip it: the case is about one thing. A case that the reference fails is either wrong or a finding; read the trace before deciding which, and if it is a finding, Lab C's issue template is for it.

Then change your table and watch the derivation hold, as with the example: flip the one condition the defect turns on and see which fields of the expected trace follow; make two items agree and see the case stop isolating; change the route's `on_unresolved` and see what else moves.

**Checkpoint 3.** Your defect, the rule it breaks, the first differing field, and the count from `--all-defects`.

## Part 4. Lab B: the specification's own checker (30 minutes)

A pull request that adds a case has to pass `conformance/check.py`: every case against the schemas, its digest against the definition, a refusal with no payload file, reason codes against the requirements, and the listed implementations' stored reports against the corpus as it now stands.

```sh
export CWA_SIBLINGS_ROOT=..               # wherever the siblings are checked out
uv run spec_check.py --case <your id>     # copies the spec sibling to scratch, adds your case, runs check.py
uv run spec_check.py --keep ...           # keep the copy to branch from
```

The sibling checkout is never modified. Try breaking the case on purpose in the scratch copy: edit the digest in `expected.trace.json`, run `python3 conformance/check.py` there, then put a stray `expected.payload.txt` beside a refusal and run it again.

Now the last question: does the corpus already cover your defect? The manifest's `breaks` list names the published cases that do, for the ten; for an uncovered defect, `spec_check.py` refusing a duplicate id, or a published case with your decisions in it, tells you the corpus caught up. Either way the comparison is the lesson: did the published case intend the same decisions you did, and does yours isolate the defect more narrowly or less? A case that duplicates a published one is not a pull request; a case that isolates a defect the published one only reaches by accident may be.

**Checkpoint 4.** What `check.py` printed with your case added, which published case (if any) covers your defect, and how yours compares.

## Part 5. Lab C: writing to the project (45 minutes)

The project takes three kinds of issue, each with a template in `.github/ISSUE_TEMPLATE/`:

| Template | For | Asks for |
| --- | --- | --- |
| A problem with a conformance case | a case whose expectation looks wrong, or that two implementations read differently | the case; what it expects and what it should, citing the rule that decides |
| A change to the specification | SPEC.md, a schema, the contract data or conformance/README.md | what should change, naming R-n or the section and what it says now; why, with a snapshot or trace that shows it |
| An implementation to list | help listing an assembler | the repository; what you need |

Questions go to Discussions. A change to what a requirement means is agreed in an issue before a diff. A pull request needs the checks green, derived text regenerated rather than edited, cases regenerated from their generators, a `CHANGES.md` bullet for any change to the specification, a new case included, and a `Signed-off-by` line on every commit (`git commit -s`). Maintainers squash-merge.

Two drafts to write, in [drafts/](drafts/):

- [case-addition.md](drafts/case-addition.md): the pull request description for a case. A worked draft for the example is there; write yours for your case, or, if Part 4 showed the corpus already covers your defect, write the case-problem issue that says whether the published case isolates it.
- [spec-change.md](drafts/spec-change.md): a change proposal in the spec-change template. The worked example proposes allowing an object for a profile's `evaluation.result`, which W6 and W7 found cannot hold a suite's result without flattening it to a string. It is written to be argued with, and its last section argues with it. Then write your own, for something a module of this repository made you want to change.

When a draft is ready to go, `uv run upstream.py --into <your fork of the specification> --case <your id>` copies the case into that checkout's `conformance/cases/` and prints the remaining steps: the checker, the generator move, the `CHANGES.md` bullet, the listed assemblers, the signed commit. It never touches git, and it is the only step of this module that leaves this repository.

**Checkpoint 5.** The two drafts, and the thing from this repository you would propose first.

## What is here

```
generate.py       the worked example: the table and the derivation; writes cases/conflict-tiebreak-not-permitted/ (--id for another id)
template.py       the same derivation with the table emptied, for your case
verify.py         the reference passes, a chosen defect (or all eleven) fails or not, first difference printed
spec_check.py     the spec sibling copied to scratch with a case added, conformance/check.py run over it
upstream.py       a case copied into a specification checkout of yours, with the pull request's remaining steps printed
cases/            the example case: case.json, snapshot.json, expected.trace.json (no payload: a refusal); yours beside it
drafts/           the pull request description and the spec-change proposal
tests/            the example is current, valid, passed by the reference, failed by its defect and specific to it
```

Facilitator run sheet: [docs/facilitator/10-conformance-contribution.md](../docs/facilitator/10-conformance-contribution.md). Worksheet: [WORKSHEET.md](WORKSHEET.md).
