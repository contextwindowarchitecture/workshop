# W3b. Framework seams

Half a day, after W3a. For engineers whose application already runs inside an agent framework and who want to know where assembly goes and how to prove it went there. Model-free: every framework runs with a recording model in place of a real one, and the proof is a hash.

A framework owns the loop: tool calls, retries, handoffs, streaming, checkpoints. It does not own the content of a model call, and most frameworks leave that blank for you to fill, with a system string and a messages array. That blank is the seam. CWA fills it with the assembled payload and nothing else. This module finds the seam in three Python frameworks, writes the three-line function that fills it, and proves for every W3a scenario that the model received exactly the payload's texts, and that a refused assembly started no run at all.

## What you leave with

- The seam, named in each framework's own API, with the verdict on whether CWA belongs there.
- A seam function per framework in [labs_seams.py](labs_seams.py), proven against W3a's committed scenarios by hash.
- A rule for your own framework: the model's input is the payload, the framework's `instructions` or `system_prompt` is empty, tools come from the grant, and a refusal is decided before the framework starts.

## Part 1. The seam in five frameworks (30 minutes)

The Assembler page's [framework picker](https://contextwindowarchitecture.io/assembler.html#harness) names the seam for each. Python here; the others are call-outs.

| Framework | Where the seam is | Verdict |
| --- | --- | --- |
| OpenAI Agents SDK | `RunConfig(call_model_input_filter=...)`: a hook that runs before every model call and returns the call's input. The agent's `instructions` callable must return nothing: whatever it returns takes the system role, which only governance may take | Yes, through the filter. The dynamic instructions callable was already a context assembler without a spec. |
| LangGraph | the node that turns state into messages: `def call_model(state): messages, trace = assemble_context(state)`. The graph gives order of operations; it says nothing about order of context | Yes. The checkpoint is already `state.task`. |
| LangChain `create_agent` | a `@wrap_model_call` middleware that overrides the request's `system_message` and `messages`. The agent's `system_prompt` must not reach the model | Yes, the same seam one layer up. The agent takes one system message, so the entries join with one separator. |
| Claude Agent SDK | `ClaudeAgentOptions.system_prompt` and the prompt handed to `query()`: the two places the SDK takes text. Tools stay with `allowed_tools`, enforced outside the model | Yes, most of all here: compaction decides what survives, and CWA's tiers decide what it is choosing between. Not driven model-free here; the mapping is written and tested. |
| Vercel AI SDK (TypeScript) | `streamText({ system, messages, tools })`, with `system` and `messages` from the assembler | Yes. The SDK is unopinionated about content on purpose; CWA is the opinion, in one module beside the route. Call-out only in this Python module. |
| Your own loop | `build_messages(user, query, docs, history)`: rename it `assemble_context` | Yes, and the cheapest adoption: you already have an assembler without a spec. W3a's `provider.py` is this seam. |

When to skip it, in this module's judgement rather than the website's: a single prompt with one owner, no retrieval, no memory and no tools, where the whole context fits on a screen and never changes between calls; a throwaway prototype measured only by whether it works once; and the case where the framework's own context management is the thing under evaluation. In each, there is nothing for a trace to explain. The moment two sources can disagree, or a budget can be exceeded, or someone asks "what did the model see", the seam is worth filling.

**Checkpoint 1.** For the framework you use, the seam in its API and the two things that must be left empty.

## Part 2. The proof (20 minutes)

```sh
uv sync                       # installs the Agents SDK, LangGraph and LangChain; a minute on a warm cache
uv run prove.py               # every W3a scenario through every seam, with recording models
uv run pytest
```

[frameworks.py](frameworks.py) runs each framework with a recording model: an Agents SDK `Model` and a LangChain `BaseChatModel` that write down what they are given and answer with a fixed text. For each W3a scenario the table says whether what the model received hashes to the payload's texts. For the refused scenario (the off-topic question, `evidence_required`) it says `no call`: the application decided before the framework started, and no recording model was called. The hashes are committed in [scenarios/proof.json](scenarios/proof.json), so a framework upgrade that changes what reaches the model fails the build.

Read [common.py](common.py): `assemble_context()` is W3a's freeze and assemble, unchanged. `texts_of()` is what a payload says the model should get. Nothing in this module builds context; it only hands it over.

**Checkpoint 2.** The two hashes for one scenario, and why the middleware column says `same, joined`.

## Part 3. The lab: three seams (60 minutes)

```sh
export CWA_W3B_IMPL=labs
uv run prove.py               # not written yet
uv run pytest                 # 14 fail until the seams are right
```

Write the three functions in [labs_seams.py](labs_seams.py). Each takes the payload bytes and returns one framework's input. The rules are the same three in each:

1. **Every system entry becomes a system message**, in order. Where the framework takes one system message, join them with one separator and nothing else; the separator is the only text the seam adds, and the Claude mapping names it so a reviewer can see it.
2. **The one user message becomes the one user message.** `cwa-messages/v1` renders exactly one, and the history the route admitted is already inside it as `interaction.history` items. `state["messages"]` and the framework's session are not the model's input.
3. **Nothing else.** No "Answer in JSON", no date, no persona. The agent's `instructions` and `system_prompt` are left empty and the tests check that a sentinel in them never reaches the model. Tools come from the capability grant (W5), not from the framework's tool list.

The Agents SDK seam returns `(items, None)`: the input list and an empty `instructions`. The LangGraph seam returns `SystemMessage` and `HumanMessage` objects. The Claude seam returns the two strings and the separator. [solution_seams.py](solution_seams.py) is the reference.

**Checkpoint 3.** The first test that failed, and what text had reached the model.

## Part 4. Your framework (30 minutes)

On the worksheet: the seam in your framework's API; what it does with history between calls and whether that is the model's input or the application's state; where its tool list comes from and whether a grant could drive it; what happens when the seam raises or returns nothing, which is where a refusal goes. Then the one-line verdict, and whether you would file an issue with the framework for a seam it lacks.

## What is here

```
common.py           W3a's assemble_context, texts_of (what a payload says the model gets), joined, digest
frameworks.py       the recording models and one run_* per framework; SEAMS, JOINS_SYSTEM, expected_for
labs_seams.py       your three seam functions; solution_seams.py the reference; seam_impl.py selects (CWA_W3B_IMPL)
prove.py            the table; scenarios.py --check / --write keeps scenarios/proof.json current
tests/              every seam on every W3a scenario; a refusal calls no model; the sentinel never reaches the model
```

The seams build on W3a's application one directory up, which is why this directory's selector is `seam_impl.py` and its modules are flat: W3a's `impl.py`, `solution/` and `scenarios.py` share the import path.

Facilitator run sheet: [docs/facilitator/03b-framework-seams.md](../../docs/facilitator/03b-framework-seams.md). Worksheet: [WORKSHEET.md](WORKSHEET.md).
