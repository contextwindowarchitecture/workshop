"""The triage briefing's producers, ported from integrations/fullsend/briefing/{governance,triage}.go.

Each reads one source of the forge read with read-level credentials and proposes items. Who wrote a comment decides its
slot and authority, never what the comment says (R-1, R-7, R-10): repository permission at or above the route's
threshold may instruct, fullsend's own earlier comments are its prior turns, and everything else is material.
"""

from __future__ import annotations

from typing import Any

from briefing import batch, freeze, instant, new_item

Batch = dict[str, Any]


def governance(r: dict[str, Any]) -> list[Batch]:
    """The two governing batches every route admits. Each source is pinned and verified: the agent definition and its
    output contract at the SHA the config pins, and AGENTS.md at the protected base branch's SHA, never the PR head."""
    def gov(item: dict[str, Any], eligibility: str) -> dict[str, Any]:
        return {**item, "trust": "verified", "injection_risk": "none", "lineage": "verbatim", "eligibility": eligibility}

    a, c = r["agent"], r["output_contract"]
    registry = [
        gov(new_item(f"agent:{a['name']}@{a['sha']}", "governance.instructions", a["source"], a["sha"], "governing", r["read_at"], a["body"]),
            "agent definition pinned by sha in .fullsend/config.yaml"),
        gov(new_item(f"contract:{c['id']}/{c['version']}", "governance.output_contract", f"fullsend-ai/agents/schemas/{c['id']}.json",
                     c["version"], "governing", r["read_at"], c["body"]), "harness validation_loop.schema (ADR 0022)"),
    ]
    if r.get("example"):
        e = r["example"]
        registry.append(gov(new_item(e["id"], "governance.examples", "fullsend-ai/agents/examples/triage", a["sha"], "governing", r["read_at"], e["body"]),
                            "steering example for the decision vocabulary"))
    md = r["repo_agents_md"]
    repo = [gov(new_item(f"repo:{md['path']}@{r['base_sha']}", "governance.instructions", f"{r['repo']}/{md['path']}", r["base_sha"], "governing",
                         r["read_at"], md["body"]), "read from the protected base branch at a pinned SHA, never from the PR head")]
    return [batch("agent-registry", "policy", registry), batch("repo-policy", "policy", repo)]


def query(r: dict[str, Any], task: dict[str, str], id: str, at: str, body: str) -> Batch:
    """The live task statement. Dispatch writes it from the normalized event; it is never copied from issue text, so a
    work item's author cannot become the user the agent answers to (R-7)."""
    item = new_item(id, "interaction.query", f"dispatch:{r['repo']}/runs/{r['run_id']}", "normevent/v1", "user", at, body,
                    trust="verified", injection_risk="untrusted_content", scope=task, eligibility="templated from the normalized event")
    return batch("dispatch", "interaction", [item])


def triage_state(r: dict[str, Any], task: dict[str, str]) -> Batch:
    """Application-written and current (R-8): the work item's status and labels, and who triggered the run with what
    permission. A cached read older than the route's max_age_seconds is excluded by the assembler as stale_state."""
    iss, trig = r["issue"], r["trigger"]
    user = {"tenant": r["repo"], "user": trig["actor"]}
    work_item = new_item("state:work-item", "state.task", f"forge:{r['repo']}/issues/{iss['number']}", iss["updated_at"], "state", r["read_at"],
                         f"issue {r['repo']}#{iss['number']} · {iss['state']} · labels: {', '.join(iss['labels'])} · title: {iss['title']} · "
                         f"opened {iss['created_at']} by @{iss['author']} (permission: {iss['author_permission']})",
                         scope=task, eligibility="forge read at freeze time")
    requester = new_item("state:requester", "state.user", f"forge:{r['repo']}/collaborators/{trig['actor']}", trig["at"], "state", r["read_at"],
                         f"@{trig['actor']} triggered this run ({trig['kind']} {trig['label']}) with repository permission '{trig['actor_permission']}', "
                         "resolved by the authorization contract (ADR 0054).", scope=user, eligibility="dispatch authorization result")
    items = [work_item, requester]
    for s in r.get("stale_reads", []):
        items.append(new_item(s["id"], "state.task", f"forge:{r['repo']}/checks", r["base_sha"][:7], "state", s["read_at"], s["body"],
                              scope=task, eligibility="cached CI summary"))
    return batch("forge-state", "state", items)


def thread(r: dict[str, Any], task: dict[str, str]) -> list[Batch]:
    """The issue and its comments split by who wrote them, never by what they say (ADR 0098 actor provenance becomes
    CWA authority): fullsend's own comments are prior model turns (history, untrusted, lineage generated); actors at or
    above the route's threshold may instruct (history, user); everything else is material (evidence.tool_results,
    observation), where the route caps floods per author."""
    iss = r["issue"]
    turns = [{"id": 0, "author": iss["author"], "permission": iss["author_permission"], "bot": False, "created_at": iss["created_at"],
              "body": iss["title"] + "\n\n" + iss["body"]}] + list(r["comments"])
    history, observed = [], []
    for t in turns:
        is_body = t["id"] == 0
        ref = "body" if is_body else str(t["id"])
        source = f"forge:issue/{iss['number']}/body" if is_body else f"forge:issue/{iss['number']}/by/{t['author']}"
        if t["bot"]:
            item = new_item(f"turn:comment/{ref}", "interaction.history", source, ref, "untrusted", t["created_at"], t["body"],
                            lineage="generated", eligibility="fullsend's own earlier comment")
        elif t["permission"] in r["triage_permission_threshold"]:
            item = new_item(f"turn:comment/{ref}@{t['author']}", "interaction.history", source, ref, "user", t["created_at"], t["body"],
                            eligibility=f"author permission '{t['permission']}' >= triage")
        else:
            # The renderer orders a slot's items by id (only history goes by time), so ids that sort in thread order keep
            # the issue body ahead of its comments.
            pos = "0-body" if is_body else "c" + ref
            item = new_item(f"obs:issue/{iss['number']}/{pos}@{t['author']}", "evidence.tool_results", source, ref, "observation", t["created_at"],
                            t["body"], eligibility=f"author permission '{t['permission']}' below triage: data only")
        item.update(injection_risk="untrusted_content", scope=task)
        (history if item["slot"] == "interaction.history" else observed).append(item)
    return [batch("forge-thread", "interaction", history), batch("forge-observer", "retrieval", observed)]


def duplicates(r: dict[str, Any]) -> Batch:
    """The similarity index's result: one scored item per candidate, never a merged list (R-13)."""
    items = [new_item(f"dup:issue/{d['number']}", "evidence.knowledge", f"forge:issue/{d['number']}", d["updated_at"], "reference_only", d["updated_at"],
                      f"#{d['number']} ({d['state']}) {d['title']}: {d['excerpt']}", relevance=d["score"], injection_risk="untrusted_content",
                      scope={"tenant": r["repo"]}, eligibility="similarity score from the duplicate index")
             for d in r["duplicate_candidates"]]
    return batch("duplicate-index", "retrieval", items)


def triage_memory(r: dict[str, Any], task: dict[str, str]) -> Batch:
    """This agent's earlier conclusions on the work item. Each expires and names its source run; one already expired is
    not emitted but reported, so the trace still shows it (R-9, R-14)."""
    items, expired = [], []
    for m in r["memory"]:
        id = f"run:triage/{m['run']}#summary"
        if not instant(m["expires"]) > instant(r["assembly_time"]):
            expired.append({"item_id": id, "reason": "expired", "stage": "producer"})
            continue
        items.append(new_item(id, "interaction.memory", f"run:triage/{m['run']}", m["run"], "generated", m["at"], m["summary"],
                              expires=m["expires"], lineage="summarised", injection_risk="untrusted_content", scope=task,
                              eligibility="this agent's own earlier run on this work item"))
    return batch("run-memory", "memory", items, expired)


def triage(r: dict[str, Any], route: dict[str, Any], profile: dict[str, Any], input: int) -> dict[str, Any]:
    """The frozen snapshot for a triage run on the route policy and profile, with `input` tokens of briefing."""
    iss, trig = r["issue"], r["trigger"]
    task = {"tenant": r["repo"], "task": f"issue:{iss['number']}"}
    scope = {"tenant": r["repo"], "user": trig["actor"], "session": "run:" + r["run_id"], "task": task["task"], "step": "triage"}
    batches = governance(r) + [triage_state(r, task),
                               query(r, task, f"query:triage/run-{r['run_id']}", trig["at"],
                                     f"Triage {r['repo']}#{iss['number']}. This run was triggered by @{trig['actor']} adding the label '{trig['label']}'. "
                                     "Decide using the material provided and answer with the triage result object.")]
    batches += thread(r, task)
    batches += [duplicates(r), triage_memory(r, task)]
    return freeze(r, scope, route, profile, input, batches, None)
