# W9 module B. The assembler adapter protocol and the harness

Half a day, self-paced, model-free. You leave able to put any assembler behind the protocol every runner in the ecosystem speaks, and to judge any assembler by the published pass rule without reading its code.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` installs the reference assembler. No sibling is needed for the lab; the four-way agreement at the end needs `assembler-demo` built. Each port's adapter command is in [docs/assemblers.md](../../docs/assemblers.md).
- W1. W8 helps: this is the protocol the kata's runner used.
- Open [worksheet.md](worksheet.md) beside this file.

Conference cut (75 minutes): part 1 and the lab.

## The protocol

A runner that tests an assembler must not import it: it has to drive a Go binary, a Rust binary, a Node process and a Python process the same way. The protocol is small. Snapshot bytes on stdin. Exit 0 when the assembler assembled or refused, with one JSON object on stdout, `{"payload": <base64 or null>, "trace": {...}}`. Exit 2 when the snapshot is rejected before assembly, the problems on stderr. Exit 3 when an otherwise valid snapshot names a tokenizer or renderer the assembler does not provide, with exactly `<component> <id> is not provided` on stderr. Nothing else on stdout, ever.

Three exits for the three kinds of outcome a black box must tell apart; base64 so the payload's bytes survive a text channel; a fixed sentence for exit 3 so a runner can tell an optional component from a required one and record `skipped` rather than `failed`.

## Part 1. Drive the reference (20 minutes)

```sh
uv sync
uv run harness.py run ../../shared/contract/cwa/conformance/cases/fixture-three-slot/snapshot.json
uv run harness.py run ../../shared/contract/cwa/conformance/cases/required-slot-missing/snapshot.json
uv run harness.py run ../../shared/contract/cwa/conformance/rejections/producer-in-two-batches/snapshot.json
```

Assembled, refused, rejected: the harness reports the exit it saw, the digest, and the hash or the refusal reason. Then the whole suite through the solution's adapter:

```sh
uv run harness.py conformance
```

Sixty-five cases and twenty-five rejections, judged by the published rule: payload bytes equal, trace equal field for field with `trace_id`, `timings` and `recovery.detail` removed, and a case that needs an optional component the adapter lacks skipped rather than failed. The report it writes is in the published `conformance_report.schema.json` shape, naming the contract commit from the lock.

**Checkpoint 1.** The worksheet's three outcomes with their exit codes and what was on each stream.

## The lab. Write the adapter (60 minutes)

Open [labs/adapter.py](labs/adapter.py). About thirty lines; the docstring is the specification.

```sh
CWA_W9B_IMPL=labs uv run pytest tests/test_lab_adapter.py
uv run harness.py conformance --impl labs
```

The tests cover the cases people get wrong: a stray print to stdout; a non-JSON input treated as a crash rather than a rejection; the exit 3 sentence worded differently; and the order of checks, because `Snapshot.from_json` validates first and resolves components after, so a snapshot that breaks its schema is rejected even when it also names a missing renderer.

**Checkpoint 2.** Your adapter passing the suite, and the one line that decides between exit 2 and exit 3.

## Part 3. Compare, disagree, agree (40 minutes)

The harness compares several adapters on the same bytes and reports the first difference as a JSON pointer, in UTF-16 key order:

```sh
uv run harness.py compare ../../shared/contract/cwa/conformance/cases/fixture-three-slot --adapter "uv run --quiet python solution/adapter.py" --adapter "uv run --quiet python labs/adapter.py"
```

Then break one on purpose: change a token count in a copy of an expected trace and watch the pointer name `/included/0/tokens`. `tests/test_harness.py` does this for you. If the `assembler-demo` sibling is built, add the other three implementations and run a four-way agreement on any snapshot:

```sh
D=$(python3 ../../shared/siblings.py assembler-demo)
uv run harness.py agreement ../../shared/contract/cwa/conformance/cases/messages-render/snapshot.json \
  --adapter "uv run --quiet python solution/adapter.py" --adapter "$D/bin/cwa-adapter-go" --adapter "$D/bin/cwa-adapter-rust" --adapter "node $D/adapters/typescript_adapter.mjs"
```

Four languages, one payload hash. When they disagree, the pointer says where, and that is a bug in one of them or a gap in the specification; W10 is where it goes.

**Checkpoint 3.** The pointer you got from the broken expectation, and, if you ran it, the four-way result.

## After this module

- Add your own assembler, in any language, behind the same protocol and run the suite against it.
- W10 takes a disagreement to the specification repository as a case.

## Covers

R-17 (the three outcomes), R-21 and R-23 (the pass rule), §1 (what a conformance claim rests on).

## Files

- `labs/adapter.py`: the lab. `solution/adapter.py`: finished, which CI uses.
- `harness.py`: run, compare, conformance, agreement. `conformance-report.json`: the committed report from the solution adapter; `scenarios.py --check` regenerates and compares it.
- `tests/`: the protocol tests and the harness tests.
