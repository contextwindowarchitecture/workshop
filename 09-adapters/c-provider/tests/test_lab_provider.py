"""The adapter hands the payload over unchanged. CWA_W9C_IMPL=labs runs these against yours."""

from __future__ import annotations

import json

import pytest

import impl
import payloads


@pytest.fixture
def provider():
    return impl.module()


@pytest.fixture(params=[payloads.MESSAGES, payloads.BLOCKS], ids=["messages", "blocks"])
def result(request):
    return payloads.rendered(request.param)


def test_system_entries_become_system_messages_in_order(provider, result):
    ir = json.loads(result.payload)
    request = provider.to_request(result.payload, "m", 1200)
    system = [m["content"] for m in request["messages"] if m["role"] == "system"]
    assert system == [e["text"] for e in ir["system"]]


def test_the_user_message_is_the_payloads_text_and_the_only_live_turn(provider, result):
    ir = json.loads(result.payload)
    request = provider.to_request(result.payload, "m", 1200)
    users = [m for m in request["messages"] if m["role"] != "system"]
    assert len(users) == 1 and users[0]["role"] == "user"
    content = ir["messages"][0]["content"]
    expected = content if isinstance(content, str) else "".join(b["text"] for b in content)
    assert users[0]["content"] == expected
    assert "<history id=" in users[0]["content"], "prior turns ride inside the single user message, never as messages of their own (R-7)"


def test_tools_come_from_the_tools_channel_and_max_tokens_from_reserved_output(provider, result):
    ir = json.loads(result.payload)
    request = provider.to_request(result.payload, "m", payloads.reserved_output())
    assert request["max_tokens"] == payloads.reserved_output() and request["model"] == "m"
    assert [t["function"]["name"] for t in request["tools"]] == [json.loads(e["text"])["name"] for e in ir["tools"]]
    assert all(t["type"] == "function" for t in request["tools"])


def test_no_text_is_added_removed_or_changed(provider, result):
    request = provider.to_request(result.payload, "m", 1200)
    assert provider.digest(provider.texts_of_request(request)) == provider.digest(provider.texts_of(result.payload))


def test_blocks_and_messages_carry_the_same_texts(provider):
    a = provider.to_request(payloads.rendered(payloads.MESSAGES).payload, "m", 1)
    b = provider.to_request(payloads.rendered(payloads.BLOCKS).payload, "m", 1)
    assert [m["content"] for m in a["messages"]] == [m["content"] for m in b["messages"]]


def test_a_refusal_has_no_request(provider):
    assert payloads.refused().payload is None  # nothing to adapt: the application sends nothing (R-17)


def test_the_snippet_contains_the_request(provider):
    result = payloads.rendered()
    request = provider.to_request(result.payload, "m", 1200)
    text = provider.snippet(request)
    assert "chat.completions.create" in text and json.loads(result.payload)["system"][0]["text"][:40] in text


def test_a_cache_breakpoint_is_structure_not_text():
    from solution import provider as reference
    result = payloads.rendered(payloads.BLOCKS)
    ir = json.loads(result.payload)
    some_block = ir["messages"][0]["content"][2]["id"]
    with_bp = reference.to_anthropic_request(result.payload, "m", 1200, breakpoint_after=some_block)
    without = reference.to_anthropic_request(result.payload, "m", 1200)
    texts = lambda r: [b["text"] for b in r["messages"][0]["content"]]
    assert texts(with_bp) == texts(without)
    assert sum("cache_control" in b for b in with_bp["messages"][0]["content"]) == 1
