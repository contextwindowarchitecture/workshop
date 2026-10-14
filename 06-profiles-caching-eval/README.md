# W6. Placement profiles, prompt caching and profile evaluation

Half a day, self-paced, model-free. You leave with one evaluated profile whose evaluation points at a reproducible artifact, a registry lock the team can ship, and a deployment gate that refuses the other candidates.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` installs the reference assembler and the OpenAI SDK. The live part of the suite is optional and needs an endpoint.
- W1. W3a or W4 helps: this is that application, with three candidate placements for its route.
- Open [worksheet.md](worksheet.md) beside this file. The website's [Placement](https://contextwindowarchitecture.io/evidence.html) page has the evidence, the profile format and the evaluation protocol; this module runs the experiments locally.

Conference cut (90 minutes): part 1 and Lab B.

## Where things go is not the spec's business

CWA takes no position on placement. It requires that placement be a **profile**: versioned, per route, evaluated against that route's tasks before it is promoted, and recorded in every trace (R-19, R-20). The Placement page collects the evidence for that position: three papers that measure where attention goes and find that it varies with model, length and task, two provider guides that disagree about where instructions go, and two prompt-cache mechanisms that agree on one thing, that a cache reuses only an unchanged prefix.

So a profile is a hypothesis, and the evaluation is the experiment. The six-step protocol on the Placement page is the lab plan here: fix the item set, name the metric, render with each profile, compare on the target model, measure reuse, record and version.

## Part 1. Three placements, one item set (20 minutes)

```sh
uv sync
uv run profiles.py list --impl labs
uv run profiles.py diff policy-first cache-first --impl labs
```

[labs/profiles.json](labs/profiles.json) holds three candidates for the `account-help` route. They place the same six slots. `policy-first` puts the articles before the memory and the history; `evidence-first` puts them right after the instructions; `cache-first` puts everything that is stable across a conversation first and everything that changes per turn, the articles and the query, last. The diff renders the same request under two of them: the same item set in a different order, so different bytes and a different hash.

**Checkpoint 1.** The worksheet's part 1 table: the three orders and what differs.

## Lab B. Measure reuse (45 minutes)

A provider's prompt cache reuses an unchanged prefix, at block boundaries. The `cwa-message-blocks/v1` renderer emits the user message as one block per item so a breakpoint can sit between any two (R-7). Over a frozen four-turn conversation, measure how many leading blocks of turn n reappear unchanged at the head of turn n+1:

```sh
uv run evaluate.py reuse cache-first
uv run evaluate.py reuse policy-first
uv run evaluate.py reuse evidence-first
uv run evaluate.py compare
```

Under `cache-first` the shared prefix grows with the conversation, five blocks, then seven, then nine, because history renders in the order it was said (R-7) and each turn appends. Under `policy-first` it stops at three on every turn, at the first article, because retrieval changes with the question. Under `evidence-first` it stops at one. The §6.1 cache-reuse test is `tests/test_reuse.py`: a breakpoint placed after the history on one call is still valid on the next.

| Profile | Block reuse | Evidence distance (tokens) |
| --- | --- | --- |
| policy-first | 0.26 | 87 |
| evidence-first | 0.09 | 127 |
| cache-first | 0.57 | 0 |

The third column is what `cache-first` trades for its reuse: the articles sit right before the query, far from the instructions. Whether that helps or hurts the answer is the question only a model can settle, and that is Lab C's live part.

**Checkpoint 2.** The worksheet's reuse numbers from your own run, and why the shared prefix grows under one profile and not the others.

## Lab C. Evaluate and promote (60 minutes)

The suite is `w6-structural/v1`: block reuse, byte reuse, evidence distance and tokens over the three frozen conversations in `evaluations/conversations.json`, deterministic and model-free. With `--live` it also asks a model each turn and grades whether every article id the answer cites was in the request.

```sh
uv run evaluate.py run cache-first --impl labs
uv run evaluate.py run policy-first --impl labs
uv run evaluate.py run evidence-first --impl labs
uv run evaluate.py promote cache-first --model-family <your model> --impl labs
CWA_W6_IMPL=labs uv run pytest tests/test_lab_c_evaluation.py
```

Each run writes an artifact under `evaluations/` with the suite, the profile, the date, the result and, when it ran, the live answers. Promotion writes the evaluation object into the profile, with the suite, the date, the result and the artifact path, and sets `model_family`, because a profile is evaluated for a model and not in the abstract (R-19). Naming a model family changes the profile's model target, so promotion writes the profile as its next version: cache-first v1 is promoted as cache-first v2, and its artifact stays the v1 run that evaluated it (R-20). Promoting again for the same family after a new run keeps the version, because only the evaluation changed. The structural suite alone is enough to practise the mechanism and not enough to call a profile evaluated for a model: the solution's artifact says so plainly in `live.ran: false`. With an endpoint, run `--live` and promote on that.

**Checkpoint 3.** The profile you promoted, the artifact path, and one sentence on what the live part would add.

## Lab D. Lock the registry and gate the deployment (30 minutes)

```sh
uv run registry.py digest --impl labs
uv run registry.py lock --impl labs
uv run registry.py check --impl labs
uv run registry.py deploy cache-first --impl labs
uv run registry.py deploy policy-first --impl labs
CWA_W6_IMPL=labs uv run pytest tests/test_lab_d_registry.py
```

A profile's digest covers everything except its evaluation object, so changing its placement without bumping its version changes it. Promotion sets `model_family`, which the digest covers, and that is why it writes the next version. Lock after Lab C's promotion and the lock pins cache-first v2; lock before it and the lock keeps v1 and adds v2 beside it on the next `lock` (R-20). The lock pins every profile and the route policy by digest and never rewrites an entry. A deployment asks with `deployment=True` and gets only an evaluated profile; the other two are refused with the reason (R-19, R-20). Then do the thing the lock exists for: edit a placement in `labs/profiles.json` without changing the version, run `registry.py check`, and read the refusal; put it back.

**Checkpoint 4.** The two deployment outcomes, and the refusal you got from the tampered profile.

## After this workshop

- Contribute an evaluated profile, with its artifact, as the spec repository's [CONTRIBUTING](https://github.com/contextwindowarchitecture/contextwindowarchitecture/blob/main/CONTRIBUTING.md) sets out: propose it in Discussions or an issue, then open a pull request.
- W7 puts this registry behind a deployment flag in the running application.

## Covers

R-7, R-16, R-19, R-20, R-21, R-23.

## Files

- `labs/profiles.json`, and `labs/registry.lock.json` once Lab D writes it: yours. `solution/`: the finished ones, which CI tests. `impl.py`: the `CWA_W6_IMPL` switch.
- `profiles.py`, `evaluate.py`, `registry.py`: the lab tools. `evaluations/`: the frozen conversations and the artifacts.
- `app/`: W3a's producers and a profile-parameterised freeze. `policy/`: the route policy and the instructions.
- `scenarios.py`, `scenarios/`, `tests/`: one conversation rendered turn by turn under each profile, and the tests.
