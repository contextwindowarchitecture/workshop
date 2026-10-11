"""Your port of fullsend's triage producers. The Go originals are integrations/fullsend/briefing/{governance,triage}.go;
the README's Lab 1 walks the duties. briefing.py gives new_item(), batch(), freeze(), instant(). The test of success is
exact: scenarios/triage-7811/snapshot.json must come out with the same digest, trace and payload as the Go integration.

    governance(r) -> [agent-registry batch, repo-policy batch]          policy: instructions, output contract, example; AGENTS.md at the base SHA
    query(r, task, id, at, body) -> dispatch batch                       interaction: the one query, templated by dispatch, never copied from issue text
    triage_state(r, task) -> forge-state batch                          state: the work item, the requester, and any cached read (the assembler ages it)
    thread(r, task) -> [forge-thread batch, forge-observer batch]        permission decides: bot -> history/untrusted; >= threshold -> history/user; else evidence.tool_results/observation
    duplicates(r) -> duplicate-index batch                              retrieval: one scored item per candidate
    triage_memory(r, task) -> run-memory batch                          memory: expired entries reported, not emitted
    triage(r, route, profile, input) -> snapshot                        the scope, the batches in producer-id order, freeze()
"""

from __future__ import annotations

from typing import Any

Batch = dict[str, Any]


def governance(r: dict[str, Any]) -> list[Batch]:
    raise NotImplementedError("labs/producers.py: governance")


def query(r: dict[str, Any], task: dict[str, str], id: str, at: str, body: str) -> Batch:
    raise NotImplementedError("labs/producers.py: query")


def triage_state(r: dict[str, Any], task: dict[str, str]) -> Batch:
    raise NotImplementedError("labs/producers.py: triage_state")


def thread(r: dict[str, Any], task: dict[str, str]) -> list[Batch]:
    raise NotImplementedError("labs/producers.py: thread")


def duplicates(r: dict[str, Any]) -> Batch:
    raise NotImplementedError("labs/producers.py: duplicates")


def triage_memory(r: dict[str, Any], task: dict[str, str]) -> Batch:
    raise NotImplementedError("labs/producers.py: triage_memory")


def triage(r: dict[str, Any], route: dict[str, Any], profile: dict[str, Any], input: int) -> dict[str, Any]:
    raise NotImplementedError("labs/producers.py: triage")
