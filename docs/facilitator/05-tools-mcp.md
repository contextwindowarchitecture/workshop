# W5 run sheet

Module: [05-tools-mcp/README.md](../../05-tools-mcp/README.md). Half a day self-paced; four hours instructor-led; 90 minutes as a conference cut (part 1 and Lab C). Model-free: every run uses a scripted model and a real MCP server started as a subprocess. Lab D's live recording needs an OpenAI-compatible endpoint with tool calling and is optional.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | Proposal, grant, guard: three words on one slide, and "a tool result is an observation, not permission." |
| 10 to 35 | Part 1 | Run the status check. Four tables; point at `obs:2` superseded by `obs:3` in turn 4's table, after turn 3's second poll, and at the four digests. Replay the committed run. |
| 35 to 85 | Lab A | The guard. At 75 minutes run the wrong-workspace script with a participant's guard on the projector. |
| 85 to 100 | Break | |
| 100 to 140 | Lab B | The policy. Ask the room what happens if `delete_workspace` is granted to Owners "because Ada is the Owner". |
| 140 to 185 | Lab C | The injection. Read the SYSTEM NOTICE aloud, then the two denials. Then `--fault error` and the out-of-turns script. |
| 185 to 195 | Break | |
| 195 to 225 | Lab D | Record and replay, live if an endpoint is available, else the six committed runs. |
| 225 to 240 | Close | The audit question: in your agent, what reaches the model without a grant, and what reaches a server without a guard? |

## Pre-session checks

```sh
cd 05-tools-mcp && uv sync && uv run pytest && uv run scenarios.py --check
CWA_W5_IMPL=labs uv run pytest tests/test_lab_a_guard.py tests/test_lab_b_capabilities.py   # 9 fail: the labs are the starting state
uv run agent.py --replay scenarios/03-injected-instruction/run.json
```

The MCP server is a subprocess of every run and every test; a venue that blocks subprocess spawning breaks the module.

## Checkpoint answers

- **Checkpoint 1.** The clock, the task state (turn number and call list) and the observations change every turn, so every snapshot digest differs. `obs:2` is superseded by `obs:3`; both have source `mcp:fernway-accounts/get_service_status?region=EU`.
- **Checkpoint 2.** Offered on this turn; arguments are an object; arguments match the input schema; every scoped argument equals the request's scope value. The never-reason is appended because the denial becomes task state the model reads next turn, and a reason it can relay to the user is better than a bare refusal.
- **Checkpoint 3.** get_account and get_service_status to all three roles; list_members to Owner and Admin; request_plan_change to Owner; delete_workspace never. Scope `workspace: tenant` on every tool that takes a workspace. In the Ben run both mechanisms acted: the policy did not offer `list_members` (reported `capability_not_allowed` at stage producer), and when the scripted model asked anyway the guard denied it as not offered.
- **Checkpoint 4.** `delete_workspace`: check 1, not offered, never list. `request_plan_change(w_larkspur)`: check 4, the workspace is not the signed-in tenant. Next turn the task state lists both as "denied by the application" with the reasons. The observation had authority `observation` and marker `untrusted_content`, and changed nothing about any decision.
- **Checkpoint 5.** Any replay. In the committed runs, the decision worth a second look is 05: the scripted model polls four times and the application, not the model, ends it by offering no tools on the last turn.

## Stumbles

- Participants write the guard to read the question or the observation text for danger words. Redirect: the guard reads the call, the grant and the scope, nothing else.
- Participants grant `delete_workspace` to Owners. Ask what the injection scenario does then: Ada is an Owner, so the deletion would be approved. "Never" exists for actions no role should take through an assistant.
- Participants expect the injected observation to be excluded. It is admitted: it is a real observation, marked and powerless. Exclusion would hide what the endpoint did.
- `CWA_W5_IMPL` unset runs the solution. Check that they set it.
- Scripted models consume one turn per inference; a script shorter than the loop ends with "(the script ended without an answer)", which is a script bug, not an application one.
