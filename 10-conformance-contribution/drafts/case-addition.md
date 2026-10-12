# Pull request: conformance case `conflict-tiebreak-not-permitted`

A worked draft for Lab C, written for the example case against the specification at commit c252494. Tighten it, or replace it with your own for your case. If the corpus has since gained a case for this defect, this draft becomes the case-problem issue instead: does the published case isolate the defect? The maintainer's three questions are the headings.

## What gap it closes

R-11 says a freshness tie-break, when the policy sets one, decides only among several leaders. At c252494 the corpus holds a group that the tie-break decides with permission (`conflict-fact`, `f-freshness`) and a group with two leaders at the same instant and no permission (`f-tie`), where the clock could not decide in any case. It holds no group with two leaders at different instants and no permission. An assembler that applies the tie-break whenever leaders differ in freshness, permission or not, passes every published case.

This case has two leaders from the top-ranked producer, `kb:window-1` at 2026-09-12T15:30:00Z and `kb:window-2` at 2026-09-13T09:00:00Z, under a fact policy with `precedence: ["policy-corpus"]`, no `freshness_tiebreak`, and `on_unresolved: refuse`. It expects `decided_by: escalated`, `resolution: refused`, and a refusal with `conflict_unresolved`. An assembler that breaks the tie by the clock records `decided_by: freshness`, excludes `kb:window-1` with `conflict_lost`, and assembles.

## What it says about the rule as written

Nothing new. The rule is explicit in R-11 and in conformance/README.md (Conflicts, fact groups, step 2). The case gives it a test. No requirement, schema or reason code changes, so the `CHANGES.md` bullet is a corpus entry:

> Conformance corpus: the new conflict-tiebreak-not-permitted case holds two leaders at different instants under a fact policy without `freshness_tiebreak`, which escalates and refuses. An assembler that breaks the tie by the clock without the policy's permission fails it. Implementations count it as not run until they run it. No requirement changes.

## What every listed assembler did with it

Run each listed assembler against the case before opening the pull request, through the adapter protocol (W9 module B's harness) or the implementation's own runner, and list the outcome here by implementation. The reference passes it. A listed assembler that fails it has the defect this case was written for, and the fix belongs in that implementation's repository with a link back to this pull request.

## Where the change goes

- `conformance/generators/conflicts.py`: the table joins the other fact-group cases, so `all.py` regenerates it with the rest. The workshop's standalone `generate.py` is a teaching copy and does not go upstream.
- `conformance/cases/conflict-tiebreak-not-permitted/`: the regenerated `case.json`, `snapshot.json` and `expected.trace.json`. No payload: it is a refusal.
- `CHANGES.md`: the bullet above, under the newest revision.
- `uv run python conformance/check.py` and `uv run python -m unittest discover -s conformance/tests` pass.
- Every commit signed off (`git commit -s`).
