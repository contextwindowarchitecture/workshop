"""Lab C: the suite, the artifact and the promotion. CWA_W6_IMPL=labs checks yours."""

from __future__ import annotations

import json

import evaluate
import impl
from app import context


def test_exactly_one_profile_is_promoted_with_a_reproducible_artifact(which):
    table = context.profiles(which)
    evaluated = [p for p in table.values() if p["evaluation"]["status"] == "evaluated"]
    assert len(evaluated) == 1, "evaluate the candidates, then promote one"
    chosen = evaluated[0]
    ev = chosen["evaluation"]
    assert chosen["model_family"], "a promoted profile names the model family it was evaluated for (R-19)"
    assert ev["suite"] == evaluate.SUITE and ev["date"] and ev["artifact"]
    artifact = json.loads((impl.HERE / ev["artifact"]).read_text(encoding="utf-8"))
    assert artifact["profile"] == {"id": chosen["id"], "version": chosen["version"]}
    fresh = evaluate.run(chosen, False, None)["result"]
    stored = artifact["result"]
    assert {k: v for k, v in fresh.items() if k != "grounded_answers"} == {k: v for k, v in stored.items() if k != "grounded_answers"}, "the artifact must reproduce"
    assert ev["result"] == evaluate.summarize(stored)


def test_the_promoted_profile_is_the_one_with_the_most_reuse(which):
    table = context.profiles(which)
    chosen = next(p for p in table.values() if p["evaluation"]["status"] == "evaluated")
    scores = {pid: evaluate.run(pr, False, None)["result"]["block_reuse"] for pid, pr in table.items()}
    assert scores[chosen["id"]] == max(scores.values())


def test_unevaluated_profiles_carry_no_claims(which):
    for profile in context.profiles(which).values():
        if profile["evaluation"]["status"] != "evaluated":
            assert profile["evaluation"] == {"status": "unevaluated", "suite": None, "date": None, "result": None, "artifact": None}
