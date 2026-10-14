# Capstone C1 run sheet

Kit: [capstones/scribe-diagnostic/README.md](../../capstones/scribe-diagnostic/README.md). One day, teams of three or four. Model-free throughout; a live drafter is optional at the end. Teams must have done W2, W3a and W5; W4 to W7 help. Every patient, clinician and guideline is fictional.

## Running the day

- Open with the brief and the blueprint, then run the reference on `02-transcript-injection` and `05-no-guideline`. The room should see, before writing anything, that a relayed request in the transcript gets as far as the guard and no further, and that a question the guidelines do not cover asks no model.
- Hand out `skeleton/` only. `solution/` is yours until the demo.
- Two coordination points, say both at the start: the fact `vitals.bp` asserted by `telemetry` and by the intake note in `ehr-notes`, and the grant the capability policy returns, which the freeze must put in the snapshot's `capabilities` member. Teams that split producers without agreeing on these lose an hour.
- The vitals guard is the day's best teaching moment: the application reads the trace's conflict record to learn which reading won, and holds the draft to it. Make teams find `vitals_decided()` in `app.py` and say in a sentence why the orchestrator does not compare the two bodies itself.
- The two cases each team writes are where the thinking shows. Push for one that breaks something: a draft citing the third pharyngitis paragraph that the per-source cap removed, a nurse's draft that queues a refill, a reference question on the scribe route.
- The demo question is fixed: show one trace that explains a decision a prompt could not have. The conflict group, the `capability_not_allowed` row for the nurse and the `evidence_required` refusal are the usual answers.

## Pre-session checks

```sh
cd capstones/scribe-diagnostic && uv sync && uv run pytest && uv run scenarios.py --check
CWA_C1_IMPL=skeleton uv run pytest -q 2>&1 | tail -1     # fails: the stubs raise NotImplementedError
```

## Where teams get stuck

- Putting the last recorded blood pressure in the chart item "because it is in the chart". The chart is protected state, a protected item cannot lose a conflict, and the group escalates and refuses. The reading belongs to the note that recorded it, as memory.
- Making the clinician's turns in the transcript `user`. The speech-to-text engine labelled them; nothing authenticated them. Only the typed request is the user's.
- Scoping notes to the encounter. Prior notes are from other encounters by definition; the scope's task is the patient, and the routes table says why.
- Letting the drafter's actions run. The orchestrator queues them for signature only after the screens pass, and never executes them; teams who "just call the tool" have left R-5.
- Reading the telemetry too early. A reading older than 300 seconds is `stale_state`, the conflict goes moot, and the vitals guard has nothing to hold the draft to. The fixture's readings are one or two minutes before each request.
- Raising `min_relevance` when case 05 answers. The given 3.0 already refuses it (the best paragraph for gout, the first of metformin prescribing, scores 2.58 under `common.bm25`), so an answer means the team's `guidelines` producer is not passing that score through as `relevance`. And the threshold is per route: case 05 is on `consult`, while on `scribe` anything above 3.36 drops case 04's one citation. For the reviewed policy change, show the trace for each side and let the team choose, then write the what-if note.

## After the day

Collect each team's closing section. The policy change and its evidence, the decision a prompt could not explain, and what a live model could still get wrong are the capstone's real output.
