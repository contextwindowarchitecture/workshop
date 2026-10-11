"""Lab A and Lab B: the same items under three placements, and what each placement does to cache reuse."""

from __future__ import annotations

import evaluate
from app import context


def test_profiles_differ_only_in_placement(which):
    table = context.profiles(which)
    assert set(table) == {"policy-first", "evidence-first", "cache-first"}
    slots = [sorted(p["slot"] for p in pr["placement"]) for pr in table.values()]
    assert all(s == slots[0] for s in slots), "same six slots in every profile"
    request = context.turns_of(evaluate.conversations()["export-then-roles"])[1]
    results = {pid: context.assemble(context.snapshot(request, pr)) for pid, pr in table.items()}
    item_sets = {pid: sorted(r["item_id"] for r in res.trace["included"]) for pid, res in results.items()}
    assert len({tuple(s) for s in item_sets.values()}) == 1, "placement changes nothing about admission or fitting here"
    assert len({res.trace["result"]["hash"] for res in results.values()}) == 3, "and changes every byte order"


def test_history_renders_in_the_order_it_was_said(which):
    profile = context.profiles(which)["cache-first"]
    request = context.turns_of(evaluate.conversations()["export-then-roles"])[3]
    blocks = evaluate.blocks_of(context.assemble(context.snapshot(request, profile)).payload)
    turns = [b["id"] for b in blocks if b["id"].startswith("turn:")]
    assert turns == sorted(turns) and len(turns) == 7, "six prior turns then the query, oldest first (R-7)"


def test_the_cache_first_profile_keeps_its_prefix_through_the_last_turn(which):
    table = context.profiles(which)
    conversation = evaluate.conversations()["export-then-roles"]
    cache_first = evaluate.reuse(table["cache-first"], conversation)
    policy_first = evaluate.reuse(table["policy-first"], conversation)
    shared = [p["blocks_shared"] for p in cache_first["pairs"]]
    assert shared == sorted(shared) and shared[-1] > shared[0], "under cache-first the shared prefix grows with the conversation"
    assert all(p["blocks_shared"] == policy_first["pairs"][0]["blocks_shared"] for p in policy_first["pairs"]), "under policy-first the articles break the prefix at the same place every turn"
    assert cache_first["block_reuse"] > policy_first["block_reuse"] > evaluate.reuse(table["evidence-first"], conversation)["block_reuse"]


def test_a_breakpoint_after_history_is_still_valid_on_the_next_call(which):
    """The §6.1 cache-reuse test: the leading bytes through the last turn the earlier call held are the same bytes."""
    profile = context.profiles(which)["cache-first"]
    turns = context.turns_of(evaluate.conversations()["export-then-roles"])
    earlier = evaluate.blocks_of(context.assemble(context.snapshot(turns[1], profile)).payload)
    later = evaluate.blocks_of(context.assemble(context.snapshot(turns[2], profile)).payload)
    first_article = next(n for n, b in enumerate(earlier) if b["id"].startswith("help:"))
    through_history = earlier[:first_article]  # instructions, account, memory and every history turn of the earlier call
    assert any(b["id"].startswith("turn:") for b in through_history)
    assert later[: len(through_history)] == through_history
