# W0. Context engineering foundations: the prompt is compiled output

90 minutes, self-paced. A browser and a text editor are the only tools. No code is written and nothing is installed.

By the end you can explain, in two minutes and in your own words, why a model request should be assembled from typed slots instead of concatenated, and you leave with a slot inventory of one prompt you actually own.

## Before you start

- Open the site: [contextwindowarchitecture.io](https://contextwindowarchitecture.io). If the venue has no network, a facilitator serves the `website` sibling locally (`python3 -m http.server 8000` from its directory) and every link below works with `http://localhost:8000/` in place of the site.
- Open [worksheet.md](worksheet.md) beside it, or print it. Each checkpoint writes one thing into the worksheet.
- Have one real system prompt you own ready for part 5, as text you can split and copy. You sort it by hand, so nothing leaves your machine, but use a prompt you are allowed to read closely. If you have none, part 5 gives you one.

Conference cut (45 minutes): parts 1, 2 and 5 only. Talk only (30 minutes, no lab): parts 1 and 3.

## Part 1. What goes wrong when a prompt is a string (15 minutes)

Read the home page's three screens: the opening, [the problem](https://contextwindowarchitecture.io/#shapes) and [what CWA does](https://contextwindowarchitecture.io/#assembly). The problem screen shows three failures, each with a **Reproduce** link into the simulator you use in part 2. This workshop names seven:

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

## Part 2. Reproduce the failures, then watch them not happen (20 minutes)

Open the live assembly simulator on the Assembler page at the [Support agent](https://contextwindowarchitecture.io/assembler.html#assemble/support-agent) system. It opens paused; if it is playing through the systems, press **Pause**. The simulator is illustrative, with estimated tokens and no model, but every control maps to a real decision an assembler records in a trace.

Do these in order:

1. **Budget squeeze.** The input budget starts at 8k. Step it down through 4k, 2k and 1k. At each step, note what is dropped, what is compressed to a shorter version, and what is never touched. At some point the simulator refuses instead of sending a payload: note the reason it gives.
2. **Remove a slot.** Back at 8k, click each slot in turn to remove it and read "What breaks without it". Remove the instructions, then the query, and read what happens instead of an answer. **Restore all slots** when you are done.
3. **The unassembled blob.** Press **Show the unassembled blob** and read "Symptom you'll actually see". Do the same on each of the seven system tabs, and match each system to one of part 1's failure modes. One failure mode has no system of its own; find the control in step 2 that reproduces it.
4. **Planes and slots.** Open the home page's [schema](https://contextwindowarchitecture.io/#planes) and read the four questions the planes answer: who may direct the model, what is true right now, what the model may ground on, what has happened and what is asked. Switch to **Slots**; part 5 uses this view.

**Checkpoint 2.** Fill in the matching table. Then, for three of the failure modes, write what the simulator showed and which decision prevented it. Use the simulator's words: a slot name, a tier (protected, compressible, droppable), a refusal reason, or "refused".

Expected answers include: displacement under budget is prevented because the protected slots, `governance.instructions` and `interaction.query` among them, are never touched while droppable and compressible slots give way first; authority inversion is prevented because a retrieved chunk has `reference_only` authority and nothing in its wording can change that; missing trigger becomes a refusal, `required_slot_missing`, because the query is never omitted.

## Part 3. The evidence (15 minutes)

Open [Placement](https://contextwindowarchitecture.io/evidence.html). Read the [position](https://contextwindowarchitecture.io/evidence.html#position) and [research](https://contextwindowarchitecture.io/evidence.html#research) sections and skim [caching](https://contextwindowarchitecture.io/evidence.html#caching). The page cites seven sources: three papers on where models attend and how accuracy falls with length, two provider prompting guides that disagree about where instructions go, and two provider prompt-cache pages.

The point of the page is not a recommendation. It is that CWA takes no position on where items go; it requires only that placement be a profile that is versioned, per route, evaluated against that route's tasks, and recorded in every trace.

**Checkpoint 3.** For each of the seven sources, write one sentence: what it supports, and what it does not let you conclude. One example to set the level: "Lost in the Middle supports a U-shaped attention curve on retrieval tasks for the models tested; it does not say where your instructions should go for your model."

## Part 4. Six words (10 minutes)

Open the glossary from any page's header, or read [docs/glossary.md](../docs/glossary.md). Look up exactly these six: **item**, **slot**, **snapshot**, **assembler**, **profile**, **trace**.

**Checkpoint 4.** Close the glossary and write each definition in your own words, one line each. Then reopen it and mark any of the six where your version missed something the glossary has. The usual misses: a snapshot is frozen before any model call and includes the clock; an assembler never calls a model; a trace accounts for what was left out, not only what was sent.

## Part 5. Your own prompt, in slots (25 minutes)

You sort your prompt into slots by hand. No tool does it for you, because no tool can: a slot is a decision about who owns a piece of text and what authority it carries, and the wording alone never settles that (R-7).

Keep the home page's [schema](https://contextwindowarchitecture.io/#planes) open on **Slots**, or the spec's [list of the eleven slots](https://contextwindowarchitecture.io/spec.html#s2). If you have no prompt of your own, use [sample-prompt.md](sample-prompt.md): it is the request the Fernway account assistant sends before W3 migrates it.

1. **Split.** Break the prompt into pieces, one job each. A paragraph that states an identity and a formatting rule is two pieces. A list of remembered facts or retrieved articles is one piece per entry. Headings and glue text ("Help-center articles:", "the articles below") are pieces too.
2. **Sort.** Give each piece exactly one slot, and the authority that slot carries (the table in the template). A piece no slot fits has **no owner**; write it down rather than forcing it.
3. **Write the items.** Copy [items.template.cwa.yaml](items.template.cwa.yaml) to `items.cwa.yaml` and write one item per piece that has an owner. Where you do not know a `source`, a `source_version`, a `freshness` or, for some slots, more, write `TODO`. Each `TODO` is something your application cannot currently tell an assembler.

**Checkpoint 5.** In the worksheet, record the number of pieces, how many have no owner and what they were, the number of slots you used out of eleven, and the number of `TODO` markers in your `items.cwa.yaml`. Then name the three pieces that were hardest to place: the slot you chose and the one you nearly chose. Save `items.cwa.yaml`; W1 and W3 start from it.

## Part 6. Rule zero (5 minutes)

Go back through your own prompt and find every sentence of the form "never", "always", "must", "do not". Each is a rule the prompt states. Rule zero says: language guidance goes in context, and enforceable invariants go outside the model. A rule stated in governance is an instruction; the application still has to enforce it with a guard the model cannot talk its way past.

**Checkpoint 6.** List those sentences. For each, write whether a guard outside the model could enforce it (a tool that refuses, a filter on output, a check on arguments) and, if so, what it would check. The ones with no possible guard are the ones that really are language guidance.

## After this workshop

- Bring `items.cwa.yaml` and the worksheet to [W1](../01-cwa-tour/) and [W3](../03-integration/).
- Read the home page's [harness engineering](https://contextwindowarchitecture.io/#harness) section and pick the framework you use. It shows the one stage of your loop an assembler takes over, and the decisions you are already making there without names for the parts.
- Pick a track in the [catalog](../README.md#tracks).

## Covers

R-1 (one slot and one authority per item), R-4 (slots that are never omitted), R-5 (rule zero), R-7 (no authority from wording), at the level of ideas. The Placement page and the §6.1 test table are the evidence base this workshop rests on.
