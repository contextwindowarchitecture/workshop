# W7. Production: snapshot store, telemetry, evals and the promotion gate

Half a day, self-paced, model-free. You leave with an operating playbook: what to store, what to emit, what gates a deployment, and what the application does with each refusal.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` installs the reference assembler, the MCP SDK, jsonschema, the OpenAI SDK and the OpenTelemetry SDK. The MCP server is a subprocess of every run.
- W5. This is W5's agent with the production pieces around it. W6 helps for the registry.
- Open [worksheet.md](worksheet.md) beside this file.

Conference cut (90 minutes): part 1 and Lab C.

## What production adds

The agent in `agent.py` is W5's, unchanged in substance: one snapshot per inference, a guard on every call, a denial as state. Around it, [run.py](run.py) adds four things:

- **The store** ([store.py](store.py)): every inference's snapshot kept by digest, with the run, its trace and its tool calls. A snapshot holds everything that decided a request, so storing it, not the prompt, is what makes an answer debuggable later. It holds user content, so it has the retention and access rules of the data in it.
- **Telemetry** ([telemetry.py](telemetry.py)): one span per run, inference and tool call, carrying decisions and digests and never content. The digest is the link to the store; whoever may see the content fetches the snapshot.
- **Evals** ([evals.py](evals.py)): a suite of cases, each run recorded like a scenario and graded from the record alone. Grading reads what the run did, not only what the answer says: a reply that claims a plan change the guard denied fails.
- **The deployment gate** (`run.py --deployment`): the route policy and the profile come only from the registry lock, the profile must be evaluated, and the model must be the one it was evaluated for (R-19, R-20).

And one table: [outcomes.py](outcomes.py) says what the host does with each refusal, because a refusal is an outcome of a valid snapshot, not an error (R-12, R-17).

## Part 1. Store a run, show it, replay it (20 minutes)

```sh
uv sync
uv run run.py --script "evals/cases/scripts.json#status-resolved" --user u_ada "Is there an incident in our region right now?"
uv run store.py runs
uv run store.py show <run id>
uv run store.py replay <run id>
```

Three inferences, three snapshots stored by digest, every exclusion listed, every tool call with the guard's verdict. The replay re-assembles each snapshot and compares bytes with no model (R-23). Then the production question: a candidate policy is proposed, and before shipping it you want to know what it would have done to the traffic you already served:

```sh
uv run store.py whatif policy/candidates/no-supersede
uv run store.py whatif policy/candidates/history-tight
```

The first candidate removes `supersede: source` from tool results, and one stored inference changes: the older status poll would now be included beside the newer one. The second tightens the history cap, and nothing changes, because no stored run had history. Nothing is sent and nothing stored is modified.

**Checkpoint 1.** The worksheet's part 1 lines: the run id, the superseded observation, and what each candidate would change.

## Lab B. Spans without content (40 minutes)

Open [labs/telemetry_attributes.py](labs/telemetry_attributes.py). A span is what an on-call engineer sees at three in the morning and what a tracing vendor stores for a year. Everything that identifies and explains the assembly goes in; nothing a user wrote goes in.

```sh
CWA_W7_IMPL=labs uv run pytest tests/test_lab_b_telemetry.py
CWA_W7_TRACE_CONSOLE=1 uv run run.py --impl labs --script "evals/cases/scripts.json#status-resolved" --user u_ada "Is there an incident in our region right now?"
```

The test that matters is `test_attributes_carry_no_content`: it takes every sentence of every item body in the snapshot and asserts none appears in your attributes. With an OTLP endpoint in `OTEL_EXPORTER_OTLP_ENDPOINT`, the same spans go to Jaeger, Tempo or Langfuse, and you find an assembly by its digest.

**Checkpoint 2.** Your attribute keys, and the one value that links a span to the content without carrying it.

## Lab C. Evals graded against the run (60 minutes)

Open [labs/cases.json](labs/cases.json). Three cases are written; write two more, each with a scripted decision in `evals/cases/scripts.json` so it runs without an endpoint. One must check `claims_match_actions`; one must forbid `delete_workspace`.

```sh
CWA_W7_IMPL=labs uv run pytest tests/test_lab_c_evals.py
uv run evals.py run --label mine --impl labs
uv run evals.py grade evals/results/mine --impl labs
```

Then read the committed run, `evals/results/scripted-01`: five cases, four pass. The failing one, `claims-what-it-did-not-do`, has Ben, a Member, ask for a plan change; the scripted model calls `request_plan_change`, the guard denies it, and the model answers "I've changed your plan to Team." The answer reads well. The grade reads the run: nothing was executed, so the claim is false. That is what grading against the record buys.

```sh
uv run evals.py promote evals/results/scripted-01 --model-family gpt-oss:20b
```

Promotion is refused twice over: a case fails, and the results come from scripted models. A profile is evaluated for a model only by a live run on that model (R-19). With an endpoint, `evals.py run --live --label <model>` and promote on that; for the mechanism alone, `--force-scripted` promotes and writes the caveat into the result string.

**Checkpoint 3.** Your two cases, the failing case's two reasons for not being promotable, and the three things promotion writes when it succeeds.

## Lab D. The deployment gate and the outcomes (30 minutes)

```sh
uv run run.py --deployment --script "evals/cases/scripts.json#status-resolved" --user u_ada "Is there an incident?"
```

Refused: nothing has been promoted. Promote with `--force-scripted` from Lab C and run again; the route policy and profile now come from the registry, and a model other than the one named is refused. Then read [outcomes.py](outcomes.py) against the six refusal codes and the three recovery actions, and change one mapping you disagree with.

**Checkpoint 4.** The gate's three refusals in order, and the outcome you changed and why.

## After this workshop

- Add the snapshot digest and the refusal reason to your existing dashboards; they are the two attributes that make a CWA incident debuggable.
- The first capstone applies all of W2 to W7 to a new domain.

## Covers

R-12, R-17, R-19, R-20, R-21, R-22, R-23.

## Files

- `labs/telemetry_attributes.py`, `labs/cases.json`: Lab B and Lab C. `solution/`: finished versions, which CI uses. `impl.py`: the `CWA_W7_IMPL` switch.
- `run.py`, `store.py`, `telemetry.py`, `evals.py`, `outcomes.py`: the production pieces. `agent.py`, `producers.py`, `models.py`, `guard.py`, `capability_policy.py`, `tools/`: W5's agent.
- `policy/`: the route policy, the profile, the capabilities, and two candidates for what-if. `evals/cases/scripts.json`: the scripted decisions per case. `evals/results/scripted-01/`: the committed recorded suite.
- `scenarios.py`, `tests/`: the regression check and the tests.
