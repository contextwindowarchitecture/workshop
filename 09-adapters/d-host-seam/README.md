# W9 module D. Host and framework seams

Half a day. For the owners of a host system that already decides who may speak: a code forge, a ticketing system, a chat platform, an agent runner. Model-free. Everything runs in this directory; the `integrations` sibling is optional and adds the Go original to compare against.

The worked example is [fullsend](https://github.com/contextwindowarchitecture/integrations/tree/main/fullsend), autonomous SDLC agents on Git forges, as the `integrations` repository prototypes it in Go. Today a fullsend agent starts from one prompt, "Run the agent task", and reads the issue thread itself with `gh`: a maintainer's comment, a drive-by's comment, the bot's own earlier comment and an instruction hidden in an HTML comment all arrive in one tool result. The integration moves that reading before the sandbox starts, into producers, and assembles a briefing. Repository permission decides who is `user` in the thread and whose words are evidence; the wording decides nothing.

This module ports the triage briefing's producers to Python and proves the port by digest ([docs/assemblers.md](../../docs/assemblers.md) on why the record is language-neutral): the snapshot you freeze has the digest the Go integration committed, and the Python assembler renders the same payload bytes assembler-go did. Then it uses two of the Go integration's review scenarios for the two things a host must do with a trace: score it, and act on a refusal.

## What you leave with

- The pattern for a host seam: authority from the host's permission model, the host's own identifiers as sources and versions, producers that read with read credentials before anything runs, a handoff that adds no text, and span attributes that let a run say what its agent was told.
- A port whose correctness is checked against another implementation's committed record, which is how a second language joins an integration.
- A trace scorer that flags a policy mistake no log would show, and a refusal mapped to a host outcome in the host's own words.

## Part 1. Before and after (30 minutes)

```sh
uv sync
uv run before.py             # the one tool result the agent reads today
uv run after.py --compare    # the briefing, what was left out, and the agreement with the Go record
```

The before page is the issue and its comments as `gh issue view --comments` returns them. Find the four kinds of speaker in it and notice that nothing in the text separates them.

The after page is the briefing. The agent definition is the system entries joined: the agent's own definition at a pinned SHA, the repository's `AGENTS.md` read from the protected base branch (never the PR head), the output contract. The prompt is the one user message, with a wrapper per slot: `<work_item>`, `<requester>`, `<prior_run>`, `<duplicate_candidate>`, `<thread speaker="user">` for the maintainer, `<thread speaker="assistant">` for the bot's own earlier comment, `<external_content>` for everyone below the triage threshold, and `<task_request>` last. The hidden HTML comment is in there, escaped, inside the reporter's `<external_content>`, with the agent definition saying what that wrapper means.

Left out, with the reason each row carries: the expired run summary (reported by its producer, never emitted), the duplicate candidate scoring 0.41 under the route's 0.55, the CI summary cached 20 minutes ago under a 300-second age limit, two of the three "+1" copies as exact duplicates, and the third under the per-author cap of two. The cap bounds how much one author can put in front of the agent; it is not a content filter, and what it keeps is still escaped material.

| | Today | With a briefing |
| --- | --- | --- |
| Who may instruct | nothing says | repository permission, the check the host already makes |
| A comment flood | arrives whole | collapses and is capped, each drop a trace row |
| Record of what the agent was told | none | snapshot digest, payload hash, trace; replay rebuilds the bytes |
| Too much context | degrades silently | shed in a declared order, or refused before any token is spent |

**Checkpoint 1.** The four kinds of speaker and the slot and authority each gets. The item that carries the hidden instruction, and what the model sees in its place.

## Part 2. Lab 1: the producers, ported (90 minutes)

```sh
export CWA_W9D_IMPL=labs
uv run after.py --compare      # not written yet
uv run pytest                  # six tests of the triage briefing fail until the port agrees
```

Write the seven functions in [labs/producers.py](labs/producers.py) against the Go originals in `integrations/fullsend/briefing/governance.go` and `triage.go` (the docstring lists them). [briefing.py](briefing.py) is the shared half: `new_item()` fills the eight required fields and sets trust from authority, `batch()` binds the producer identity outside the items, `freeze()` builds the snapshot with the Go package's constants, so a correct port has the same digest. The fixture [fixtures/issue-7811.json](fixtures/issue-7811.json) is the forge read; the registry holds the route policy and profile.

The duties, in the order the tests bite:

1. **Governance is pinned and verified.** The agent definition and output contract at the SHA the config pins; `AGENTS.md` at the base branch's SHA. `trust: verified`, `injection_risk: none`, `lineage: verbatim`.
2. **The query is templated by dispatch**, never copied from the issue, so an author cannot become the user the agent answers to (R-7).
3. **State is current and scoped.** The work item and the requester, read at freeze time; the cached CI summary goes in too, with its own `freshness`, and the route's `max_age_seconds` decides it (`stale_state` is the assembler's row, not yours).
4. **The thread splits by permission.** A bot comment is the agent's own prior turn: `interaction.history`, `untrusted`, `lineage: generated`. An author at or above the threshold may instruct: `interaction.history`, `user`. Everyone else is material: `evidence.tool_results`, `observation`, with ids that sort in thread order so the issue body stays ahead of its comments. All of it `injection_risk: untrusted_content`.
5. **Duplicates are one scored item each** (R-13), scoped to the tenant only.
6. **Memory expires and reports.** An entry past `expires` at assembly time is an `excluded` row with stage `producer`, not an item (R-9, R-14).
7. **Freeze.** Batches in producer-id order, scope with `step`, the budget as the briefing's share of the 200,000 window.

When the digest agrees, every field agrees: the bodies, the sources, the versions, the eligibility strings. A port that differs in one character of one body has a different digest, and the test names the scenario, not the field: that is what `after.py --compare` and the committed `scenarios/triage-7811/snapshot.json` are for. Diff yours against it.

**Checkpoint 2.** Which duty took longest, and which field the diff caught.

## Part 3. Lab 2: a scorer over traces (30 minutes)

The Go integration committed two versions of the security review under the same budget pressure. Route v1 shed memory first and lost `run:review/18990#F1`, a high-severity prior finding, as an `over_budget` row. Nothing failed; the briefing went out without it. Route v2 protects memory and sheds the docs and test diffs instead. Both traces are in [expected/](expected/).

Write `dropped_high_severity()` in [labs/score.py](labs/score.py): the ids of prior findings fitting left out. It reads the snapshot for the bodies and the trace for the decisions. Run it over both traces. The point is not the five lines; it is that a policy mistake is a query over traces, run on every run, before anyone reads what the model did.

**Checkpoint 3.** What v1 dropped, what v2 dropped instead, and the route-policy change between them (compare `fitting_order` and `tier_upgrades` in the two snapshots).

## Part 4. Lab 3: a refusal is a host outcome (30 minutes)

Starved further, route v2 refuses with `evidence_required` and recovery `precompute_summary` rather than brief a security review without the diff. Write `host_outcome()` in [labs/outcome.py](labs/outcome.py): no sandbox starts, the span carries the reason and the recovery action, and the work item gets a comment written from the trace in the host's words: what was refused, what would let a retry succeed, what was left out for budget. A model wrote none of it.

**Checkpoint 4.** The comment your mapping writes for the starved run, and the span attributes.

## Part 5. Your host (30 minutes)

Pick a system you run that already knows who may speak. On the worksheet:

- its permission model, and the authority each level maps to in `interaction.history` versus `evidence.*`;
- its identifiers, as `source` and `source_version` (a SHA, a comment id, a record version);
- the two places it already hands text to a model or agent runtime, where the handoff goes;
- one refusal and the outcome it becomes in that system;
- what the system has no source for today, which is the producers' gain rather than CWA's.

The Go integration's README has a section called "Questions a maintainer will ask". Read it before you present yours.

## What is here

```
briefing.py             new_item, batch, freeze, assemble, handoff: the shared half of the Go package, in Python
before.py / after.py    the before page; the briefing with its left-out table, span attributes and --compare
labs/, solution/        producers.py, score.py, outcome.py; CWA_W9D_IMPL selects
fixtures/               issue-7811.json, the forge read (fictional), vendored from integrations/fullsend
registry/               the triage route policy and profile, vendored
expected/               the Go integration's digests for all six scenarios, and the three review records Labs 2 and 3 read
scenarios/              the triage briefing as the solution freezes it: snapshot, trace, payload (uv run scenarios.py --check)
```

Vendored files are from [contextwindowarchitecture/integrations](https://github.com/contextwindowarchitecture/integrations) (Apache-2.0). Repositories, issues and people in them are fictional.

Facilitator run sheet: [docs/facilitator/09d-host-seam.md](../../docs/facilitator/09d-host-seam.md). Worksheet: [WORKSHEET.md](WORKSHEET.md).
