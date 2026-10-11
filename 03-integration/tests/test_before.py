"""The before app's failure modes, asserted, so the contrast stays honest when the fixtures change."""

from __future__ import annotations

import re

from before import app as before
from tests.conftest import conversation


def test_before_sends_expired_and_revoked_memories():
    system = before.build_request(conversation("01-ada-export"))["messages"][0]["content"]
    assert "Their workspace is on the Team plan." in system, "revoked in the store, pasted anyway"
    assert "Evaluating Fernway on a trial" in system, "expired in March, pasted anyway"


def test_before_sends_contradicting_claims_with_equal_standing():
    system = before.build_request(conversation("02-ben-plan-conflict"))["messages"][0]["content"]
    assert "Business plan" in system and "Team plan" in system


def test_before_answers_an_off_topic_question_from_irrelevant_articles():
    request = before.build_request(conversation("03-off-topic"))
    assert len(re.findall(r"^\[help:", request["messages"][0]["content"], re.M)) == 5, "five articles pasted in, relevant or not"
    assert request["messages"][-1]["content"].startswith("Recommend a good pizza")


def test_before_keeps_the_last_six_messages_whatever_their_size():
    request = before.build_request(conversation("04-long-conversation"))
    assert len([m for m in request["messages"] if m["role"] != "system"]) == 7
