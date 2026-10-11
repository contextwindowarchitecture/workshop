# W7 run sheet

Module: [07-production/README.md](../../07-production/README.md). Half a day self-paced; four hours instructor-led; 90 minutes as a conference cut (part 1 and Lab C). Model-free with scripted models; a live eval run and an OTLP backend are optional.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | Four pieces around an unchanged agent: store, spans, evals, gate. "Store the snapshot, not the prompt." |
| 10 to 30 | Part 1 | One run stored, shown, replayed. Then the two what-ifs; ask which candidate they would ship on that evidence. |
| 30 to 70 | Lab B | Spans. Run the no-content test on a participant's attributes with a body sentence deliberately added, so they see it catch the leak. |
| 70 to 85 | Break | |
| 85 to 145 | Lab C | Evals. Read `claims-what-it-did-not-do`'s answer aloud, then its grade. Then the promotion refusal, both reasons. |
| 145 to 155 | Break | |
| 155 to 185 | Lab D | The gate, three refusals in order; then outcomes.py and one change each. |
| 185 to 210 | Close | The playbook on one page: store, emit, gate, outcome. What their system has today. |

## Pre-session checks

```sh
cd 07-production && uv sync && uv run pytest && uv run scenarios.py --check
CWA_W7_IMPL=labs uv run pytest tests/test_lab_b_telemetry.py tests/test_lab_c_evals.py   # fail: the labs are the starting state
rm -f store/cwa.sqlite                                                                    # a clean store for the session
```

If an OTLP backend is available (Jaeger's all-in-one container is the quickest), set `OTEL_EXPORTER_OTLP_ENDPOINT` and show one assembly found by digest.

## Checkpoint answers

- **Checkpoint 1.** Three snapshots. `obs:1` superseded by `obs:2` on turn 3. `no-supersede` changes one inference, `obs:1` from excluded to included; `history-tight` changes nothing because the stored runs had no history.
- **Checkpoint 2.** The solution's keys: profile, route policy, snapshot digest, payload hash, input tokens, budget, refused, recovery, included, compressed, excluded with reasons, conflicts, defaults filled. The linking value is the snapshot digest.
- **Checkpoint 3.** Any two cases that meet the test. The failing case cannot be promoted because a case fails and because the results are scripted. A successful promotion writes the profile's `model_family`, its evaluation object pointing at the report, and the registry lock.
- **Checkpoint 4.** No lock; unevaluated profile; wrong model. Any outcome change with a reason; the one most often changed is `evidence_required` with `retrieve_narrower`, which some teams prefer to send to the user as needs-info rather than retry silently.

## Stumbles

- Participants put the question or the answer in a span "for context". The test catches the question; say why the answer is no better.
- Participants grade by reading the answer and nothing else. The failing case exists to show why that is not enough.
- `--force-scripted` is for the lab's mechanism; make sure nobody leaves thinking a scripted suite evaluates a profile for a model.
- The store file persists between runs; `store.py runs` will show everything the room has done. Clear it before and after.
- Every run starts the MCP server as a subprocess; a venue that blocks that breaks the module.
