# W3b run sheet

Module: [03-integration/seams/README.md](../../03-integration/seams/README.md). Half a day self-paced; three hours instructor-led; 45 minutes as a conference cut (part 1 and `prove.py`). Model-free. `uv sync` installs the Agents SDK, LangGraph and LangChain, a minute warm and longer cold: warm caches before the session (docs/setup.md).

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "The framework owns the loop. The blank it hands you is the seam." |
| 10 to 40 | Part 1 | The table, one row per show of hands. Read the Agents SDK verdict aloud: the instructions callable was already an assembler. |
| 40 to 60 | Part 2 | `prove.py`. Point at `no call` on the refused row and at `same, joined`. |
| 60 to 70 | Break | |
| 70 to 130 | The lab | Three functions. The usual first failure is an extra system message from the agent's instructions; the second is history pushed in as messages. |
| 130 to 160 | Part 4 | Each participant's framework on the worksheet. Collect the verdicts. |
| 160 to 180 | Close | Which seams the frameworks lack, and who files what. |

## Pre-session checks

```sh
cd 03-integration && uv sync && uv run scenarios.py --check          # W3a's scenarios, which the seams read
cd seams && uv sync && uv run prove.py && uv run pytest && uv run scenarios.py --check
CWA_W3B_IMPL=labs uv run pytest -q 2>&1 | tail -1                   # 14 fail: the stubs
```

## Checkpoint answers

- **Checkpoint 1.** Agents SDK: `RunConfig.call_model_input_filter`; leave `instructions` None and the agent's tool list to the grant. LangGraph: the `call_model` node; leave `state["messages"]` out of the model's input and the prompt template empty. LangChain: `@wrap_model_call` overriding `system_message` and `messages`; leave `system_prompt` empty. Claude SDK: `system_prompt` and the `query()` prompt; leave CLAUDE.md's rules to governance items and tools to `allowed_tools`.
- **Checkpoint 2.** Any sent scenario: the two hashes are equal for the first two columns. The middleware column is `same, joined` because `create_agent` takes one system message, so the proof compares against the entries joined with the one separator the seam adds. The refused row says `no call` in every column.
- **Checkpoint 3.** Usually `test_the_agents_instructions_never_reach_the_model` or a `langchain-middleware` row: the sentinel instructions, or the raw question pushed in beside the payload's user message.

## Stumbles

- Participants keep the agent's `instructions` "for safety" and add the system entries after it. The sentinel test catches it; ask what authority the instructions string has.
- Participants pass `state["messages"]` plus the payload. The payload already holds the admitted history; the duplicate is the displacement W1 showed.
- Participants split the joined system message back apart to make the hashes match. The seam adds a separator; say so and compare against the join, as `expected_for` does.
- Participants want to run the Claude Agent SDK live. It spawns a Claude Code process and needs credentials; the mapping is the lab.
- Framework upgrades move hooks. `scenarios/proof.json` and the pins in `pyproject.toml` are there so the build says so before a participant does.
