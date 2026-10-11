# W3a run sheet

Module: [03-integration/README.md](../../03-integration/README.md). A full day self-paced; six hours instructor-led; pairs with W1 as the one-day "migrate your app" offering when participants have done W2 beforehand, which is also its conference cut: W1's tour in the morning and parts 1 to 3 of this module in the afternoon, the guards and the lock left as homework. Model-free; no siblings; `uv sync` installs the assembler and the OpenAI SDK only.

## Timing, instructor-led

| Minutes | Step | What you do |
| --- | --- | --- |
| 0 to 15 | Framing | Run `before.app` and `solution.app` on the Ben conversation side by side. Do not explain yet; let them see "Business" and "Team" a few lines apart, then `conflict_lost`. |
| 15 to 45 | Step 1 | Inventory, on paper. Collect two and compare the slot each gave the account line. |
| 45 to 105 | Step 2 | Snapshot and assemble. Expect the first rejection; project the problems list and say that it is the to-do list. |
| 105 to 120 | Break | |
| 120 to 210 | Step 3 | Producers and conflict groups. The hard part is the facts: stop the room at 180 to show `conflict_groups()` and ask why the assembler cannot find the contradiction itself. |
| 210 to 240 | Step 4 | Read traces together. Everyone replays their own snapshot. |
| 240 to 300 | Lunch or long break | |
| 300 to 360 | Step 5 | Policy files. Make them defend one number each aloud: the threshold, the history cap, the margin. |
| 360 to 405 | Step 6 | Guards. The price guard is a regex; the lesson is where it runs, not what it matches. |
| 405 to 420 | Close | The conformance list. Insist on honesty about `parser: true` and profile evaluation. |

## Pre-session checks

```sh
cd 03-integration && uv sync && uv run pytest && uv run scenarios.py --check
CWA_W3_IMPL=after uv run pytest -q 2>&1 | tail -1     # should fail: the stubs raise NotImplementedError
uv run python -m before.app --conversation scenarios/03-off-topic/conversation.json | head -5
```

## Checkpoint answers

- **Step 1.** Instructions: `governance.instructions`, governing, source the file and its version. Account line: `state.user`, state, the accounts table rows and their versions. Memories: `interaction.memory`, generated, the turn each came from. Articles: `evidence.knowledge`, reference_only, the article and its version. Messages: `interaction.history`, user for the user's and untrusted for the model's. Question: `interaction.query`, user. The two "never" sentences are enforceable: a check on amounts against the evidence sent, a check for other workspace names. "Cite every article" is partly enforceable; "keep answers short" is guidance.
- **Step 3.** The memory store reports `revoked` because it knows the row is revoked and never sends it (R-14). The assembler records `conflict_lost` because resolving a declared group is admission's job and the producer could not know what the account would say (R-11). Facts come from the producers because only they know what their items assert.
- **Step 4.** Digest and hash from their own run; `missing_field:relevance`.
- **Step 5.** Threshold 3.0 is where off-topic questions score below and on-topic chunks score above on this corpus; history cap 300 tokens drops the oldest turns of the long conversation and keeps the query; margin 15% covers the estimate tokenizer's error against most model tokenizers; `budget.input` is 8192 minus 1024.
- **Step 6.** Both guards pass. The price guard blocks "$24" when only "$12" was sent; the workspace guard blocks "Larkspur Design" for Ada.
- **Done.** `parser: true` is not applicable on a chat route with no downstream parser. Profile evaluation is open: the profile is version 1 and `unevaluated`, so it cannot be deployed under R-19 until W6's work is done.

## Stumbles

- Participants copy `solution/policy/` wholesale in step 5. Allowed, but then every number is a question they must answer.
- Participants put the conflict detection in the memory producer ("I know the account says Business"). The producer does not know; the application declares and the route decides.
- Participants expect the off-topic question to refuse at step 2. It refuses only once `requires_evidence`, `min_included` and the threshold are in the route policy, in step 5. Until then it assembles with no evidence, and that is worth noticing.
- `CWA_W3_IMPL` unset runs the solution. Check that they set it.
- The before app imports `provider` and `request` from the directory root, so it must be run as a module: `python -m before.app`.
