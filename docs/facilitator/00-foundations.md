# W0 run sheet

Module: [00-foundations/README.md](../../00-foundations/README.md). Browser only. 90 minutes self-paced; 75 minutes instructor-led with the timings below; 45 minutes as a conference cut (parts 1, 2, 5); 30 minutes as a talk (parts 1, 3, no lab).

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 5 | Framing | One sentence: "a model request is compiled output, not a string you concatenate". Say what they leave with. |
| 5 to 15 | Part 1 | Walk the seven failure modes with one production story each. Ask for a show of hands per mode. |
| 15 to 35 | Part 2 | Participants drive the demo. At 25 minutes, demonstrate the bad panel yourself and read the imperative sentence aloud. |
| 35 to 45 | Part 3 | Evidence. Stress the position: no recommendation on placement, only that placement be a profile. |
| 45 to 50 | Part 4 | Six words. Pair participants to define them to each other. |
| 50 to 70 | Part 5 | Migrator on their own prompt. Circulate. |
| 70 to 75 | Part 6 and close | Rule zero. Point at the tracks in the catalog. |

## Pre-session checks

- The site loads, or the `website` sibling is served locally and you have tested the demo, the migrator and the glossary from `http://localhost:8000/`.
- The worksheet is printed or the file is open on every machine.
- You have a sample prompt ready for participants who did not bring one. The migrator's two built-in samples work.

## Checkpoint answers

- **Checkpoint 2.** Accept any three with a decision named in the demo's vocabulary. The ones to steer towards: displacement under budget is prevented by tiers, with `governance.instructions` and `interaction.query` protected and droppable slots shed first; authority inversion is prevented because a retrieved chunk carries `reference_only` and wording changes nothing; missing trigger is a refusal because the query is never omitted; redundant re-reading is addressed by placement and rendering, which the demo only hints at and W6 covers.
- **Checkpoint 3.** The common error is to turn a paper into a placement rule. Each of the three papers was run on specific models and tasks; the two provider guides disagree with each other; the two cache pages describe mechanisms, not outcomes. The right conclusion from all seven is the page's own: placement has to be evaluated per route and per model, then versioned.
- **Checkpoint 4.** Watch for: "snapshot" defined as a saved prompt (it is the frozen input to assembly, clock and policy included, taken before any model call); "assembler" defined as something that calls the model (it never does); "trace" defined as a log of what was sent (it also accounts for every exclusion with a reason).
- **Checkpoint 5.** The no-owner share for a typical hand-written prompt is between a fifth and a half. Participants who get zero have pasted a prompt that is already a single instruction. Participants who disagree with every proposed slot are usually right about at least one: the migrator proposes, it does not assign from wording, and that is a feature worth saying out loud.
- **Checkpoint 6.** Most "never" sentences in prompts are enforceable (a tool guard, an argument check, an output filter) and are currently enforced by hoping. The ones that are not enforceable (tone, register, "be concise") are the real governance text.

## Stumbles

- Participants worry the migrator uploads their prompt. It runs in the browser and sends nothing. Show the network tab if asked.
- Participants treat the landing demo as a real assembler and ask why it does not emit a trace. Say so plainly: the demo is illustrative; W1 runs the real thing and reads real traces.
- Participants want to argue about where instructions should go. Redirect to part 3's conclusion and to W6.
- Participants with no prompt of their own: use the Ada support sample, and have them disagree with its proposed slots instead.
