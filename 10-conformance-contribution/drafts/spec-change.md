# A change to the specification: a worked example, and how to argue with it

The project's spec-change template asks two things: what should change, naming the requirement, schema, reason code or README section and what it says now, and why, with a snapshot or trace that shows it. Below is an example proposal drawn from this repository's own stumbles, followed by the case against it. Write your own after it, for something a module made you want to change.

## What should change

`schema/profile.schema.json`, `evaluation.result`. It is a string today. The proposal is to allow an object as well, so a profile can carry its suite's result as structured data: the cases run, how many passed, and the threshold the gate applied.

R-19 says a profile is a draft until a published evaluation suite has been run against it, and that the trace and the profile record the evaluation's status, suite, date, result and artifact. The schema makes `result` a string.

## Why

In W4 and W6, the natural thing to record after `evaluate.py run` was the result object the suite produced: `{"cases": 6, "passed": 6, "threshold": 1.0}`. The schema rejected it, and both modules flatten the result to a sentence before writing the profile. A reviewer reading the registry then has a sentence to parse where the suite had numbers, and two suites can word the same result differently, so the registry cannot be queried for "every profile whose suite passed under threshold" without reading each sentence.

A profile that shows it:

```json
"evaluation": {"status": "evaluated", "suite": "fernway-support-evals/v1", "date": "2026-10-11",
               "result": {"cases": 6, "passed": 6, "threshold": 1.0}, "artifact": "evals/2026-10-11/report.json"}
```

The registry lock excludes `evaluation` from the profile digest, so the change does not alter any published digest. Cases that touch profiles (`registry`) would gain one with an object result; nothing else changes.

## The case against it

- The artifact already carries the structured result. `evaluation.artifact` names the report, and the report holds the numbers. `result` is the one-line reading for people, which is why a string suits it. A query over profiles belongs on the artifacts, not the registry.
- Two shapes mean every reader of a profile branches. The four assemblers and every registry tool would have to accept both. A string summary and a pointer to the data is the shape the rest of the specification uses (`recovery.detail` is free text for the same reason).
- The schema is the contract; the stumble was in the workshop. The modules now write a sentence with `summarize()`, which is what the field asks for.

Either way, the proposal is well-formed: it names the schema and what it says, it shows the profile that fails today, and it says what else would change. That is what the template needs, and what a maintainer can answer in an issue before anyone writes a diff.

## Your proposal

What should change (R-n, schema, reason code or section, and what it says now):

Why (what goes wrong as it stands, with the snapshot or trace that shows it):

What else changes (cases, schemas, CHANGES.md):
