# A change to the specification: a worked example, and how to argue with it

The project's spec-change template asks two things: what should change, naming the requirement, schema, reason code or README section and what it says now, and why, with a snapshot or trace that shows it. Below is an example proposal drawn from this repository's own stumbles, followed by the case against it. Write your own after it, for something a module made you want to change.

## What should change

`schema/profile.schema.json`, `evaluation.result`. It is a string today. The proposal is to allow an object as well, so a profile can carry its suite's result as structured data: the measurements the suite took, or the cases it ran and how many passed.

R-19 says a profile carries an evaluation object, and that promotion for a deployment requires `evaluation.status: evaluated` with a suite and version, a date, a result and a reproducible artifact location. The schema makes `result` a string or null.

## Why

In W6 and W7, the natural thing to record after a suite ran was the result it produced. W6's structural suite writes `{"block_reuse": 0.572, "byte_reuse": 0.319, "mean_evidence_distance_tokens": 0.0, "mean_input_tokens": 661.2}` into its artifact; W7's eval report counts the cases that passed. The schema accepts neither as `result`, so W6's `summarize()` flattens the object to a sentence and W7 writes "4/5 cases passed". A reviewer reading the registry then has a sentence to parse where the suite had numbers, and two suites can word the same result differently, so the registry cannot be queried for "every profile whose suite passed under threshold" without reading each sentence.

A profile that shows it:

```json
"evaluation": {"status": "evaluated", "suite": "w6-structural/v1", "date": "2026-10-11",
               "result": {"block_reuse": 0.572, "byte_reuse": 0.319, "mean_evidence_distance_tokens": 0.0, "mean_input_tokens": 661.2},
               "artifact": "evaluations/cache-first-v1-w6-structural-v1.json"}
```

The registry lock excludes `evaluation` from the profile digest, so the change does not alter any published digest. Cases that touch profiles (`registry`) would gain one with an object result; nothing else changes.

## The case against it

- The artifact already carries the structured result. `evaluation.artifact` names the report, and the report holds the numbers. `result` is the one-line reading for people, which is why a string suits it. A query over profiles belongs on the artifacts, not the registry.
- Two shapes mean every reader of a profile branches. The four assemblers and every registry tool would have to accept both. A string summary and a pointer to the data is the shape the rest of the specification uses (`recovery.detail` is free text for the same reason).
- The schema is the contract; the stumble was in the workshop. W6 writes a sentence with `summarize()` and W7 a count, which is what the field asks for.

Either way, the proposal is well-formed: it names the schema and what it says, it shows the profile that fails today, and it says what else would change. That is what the template needs, and what a maintainer can answer in an issue before anyone writes a diff.

## Your proposal

What should change (R-n, schema, reason code or section, and what it says now):

Why (what goes wrong as it stands, with the snapshot or trace that shows it):

What else changes (cases, schemas, CHANGES.md):
