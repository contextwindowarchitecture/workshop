# W0. Context engineering foundations: the prompt is compiled output

90 minutes, self-paced. A browser is the only tool. No code is written and nothing is installed.

By the end you can explain, in two minutes and in your own words, why a model request should be assembled from typed slots instead of concatenated, and you leave with a slot inventory of one prompt you actually own.

## Before you start

- Open the site: [contextwindowarchitecture.io](https://contextwindowarchitecture.io). If the venue has no network, a facilitator serves the `website` sibling locally (`python3 -m http.server 8000` from its directory) and every link below works with `http://localhost:8000/` in place of the site.
- Open [worksheet.md](worksheet.md) beside it, or print it. Each checkpoint writes one thing into the worksheet.
- Have one real system prompt you own ready to paste in part 5. The migrator runs entirely in your browser and sends nothing anywhere, but use a prompt you are allowed to read closely.

Conference cut (45 minutes): parts 1, 2 and 5 only. Talk only (30 minutes, no lab): parts 1 and 3.

## Part 1. What goes wrong when a prompt is a string (15 minutes)

Read the landing page from the top through [the problem](https://contextwindowarchitecture.io/#problem) and [why](https://contextwindowarchitecture.io/#why). Then open the **failure modes** panel. The site names seven, each reproducible on the demo:

| Failure mode | What it looks like in production |
| --- | --- |
| Authority inversion | A retrieved document, a tool result or a pasted message changes the model's behaviour because it contains imperative text |
| Instruction-shaped evidence | Evidence that reads like an instruction is followed as one |
| Stale-as-current | An old fact is presented with the same standing as a current one, and the model picks the wrong one |
| Memory that never expires | A summary or inferred preference from months ago is still steering answers, and nothing can revoke it |
| Displacement under budget | The important part of the prompt is pushed out, or truncated mid-thought, when the window fills |
| Redundant re-reading | The same text is sent again and again in a form that no cache can reuse |
| Missing trigger | The model is not told what, in all that context, it is being asked to respond to |

**Checkpoint 1.** In the worksheet, for each of the seven, write which system you have worked on that has shown it, or "not seen". You should recognise at least three. If you recognise none, pick the three you think are most likely in the next system you build.

## Part 2. Reproduce the failures, then watch them not happen (25 minutes)

Stay on the landing page and use the live assembly demo under [assemble](https://contextwindowarchitecture.io/#assemble). Pick the **Support agent** system tab. The demo is illustrative, not a real assembler, but every control maps to a real decision an assembler records in a trace.

Do these in order:

1. **Budget squeeze.** Switch the budget from 2k to 1k. Note what is dropped, what is replaced by a shorter version, and what is never touched. Then squeeze until the demo refuses rather than answers.
2. **Remove a slot.** Click each slot in turn to remove it and read the consequence. Remove the query last and read what happens when there is no trigger.
3. **The bad panel.** Open the panel that fuses everything into one blob with no assembler. Find the imperative sentence inside the retrieved text, and say which failure mode it is.
4. **Planes and slots.** Open [planes](https://contextwindowarchitecture.io/#planes) and read the four questions the planes answer: who may direct the model, what is true right now, what the model may ground on, what has happened and what is asked.
5. If you have time, take the guided tour from the header. It is sixteen stops.

**Checkpoint 2.** For three of the failure modes from part 1, write what the demo showed and which decision prevented it. Use the demo's words: a slot name, a tier (protected, compressible, droppable), a reason, or "refused".

Expected answers include: displacement under budget is prevented because `governance.instructions` and `interaction.query` are protected and droppable slots go first; authority inversion is prevented because a retrieved chunk has `reference_only` authority and nothing in its wording can change that; missing trigger becomes a refusal, because the query is never omitted.

## Part 3. The evidence (15 minutes)

Open [Placement](https://contextwindowarchitecture.io/evidence.html). Read the [research](https://contextwindowarchitecture.io/evidence.html#research) and [position](https://contextwindowarchitecture.io/evidence.html#position) sections and skim [caching](https://contextwindowarchitecture.io/evidence.html#caching). The page cites seven sources: three papers on where models attend and how accuracy falls with length, two provider prompting guides that disagree about where instructions go, and two provider prompt-cache pages.

The point of the page is not a recommendation. It is that CWA takes no position on where items go; it requires only that placement be a profile that is versioned, per route, evaluated against that route's tasks, and recorded in every trace.

**Checkpoint 3.** For each of the seven sources, write one sentence: what it supports, and what it does not let you conclude. One example to set the level: "Lost in the Middle supports a U-shaped attention curve on retrieval tasks for the models tested; it does not say where your instructions should go for your model."

## Part 4. Six words (10 minutes)

Open the glossary from any page's header, or read [docs/glossary.md](../docs/glossary.md). Look up exactly these six: **item**, **slot**, **snapshot**, **assembler**, **profile**, **trace**.

**Checkpoint 4.** Close the glossary and write each definition in your own words, one line each. Then reopen it and mark any of the six where your version missed something the glossary has. The usual misses: a snapshot is frozen before any model call and includes the clock; an assembler never calls a model; a trace accounts for what was left out, not only what was sent.

## Part 5. Your own prompt, in slots (20 minutes)

Open [Start](https://contextwindowarchitecture.io/start.html#migrate). The migrator takes a system prompt or a message array and proposes slots and items. Try the two samples first, then replace them with your own prompt.

Read the result. It shows the share of estimated tokens the rules could not assign to any slot ("no owner"), the items it proposed with a default authority each, and an export, `items.cwa.yaml`, where every item still has `TODO` where a `source`, a `source_version`, a `freshness` and, for some slots, more are missing. The migrator does not assign slots from the wording of your prompt. It proposes; you decide.

**Checkpoint 5.** In the worksheet, record the no-owner figure, the number of items proposed, the number of `TODO` markers in the export, and three items whose proposed slot you disagree with and the slot you would give them. Save the export; W1 and W3 start from it.

## Part 6. Rule zero (5 minutes)

Go back through your own prompt and find every sentence of the form "never", "always", "must", "do not". Each is a rule the prompt states. Rule zero says: language guidance goes in context, and enforceable invariants go outside the model. A rule stated in governance is an instruction; the application still has to enforce it with a guard the model cannot talk its way past.

**Checkpoint 6.** List those sentences. For each, write whether a guard outside the model could enforce it (a tool that refuses, a filter on output, a check on arguments) and, if so, what it would check. The ones with no possible guard are the ones that really are language guidance.

## After this workshop

- Bring `items.cwa.yaml` and the worksheet to [W1](../01-cwa-tour/) and [W3](../03-integration/).
- Read the Start page's six steps and mark which your team already does. Most teams find they do steps 1 and 6 partly and none of 2 to 5.
- Pick a track in the [catalog](../README.md#tracks).

## Covers

R-1 (one slot and one authority per item), R-5 (rule zero), R-7 (no authority from wording), at the level of ideas. The Placement page and the §6.1 test table are the evidence base this workshop rests on.
