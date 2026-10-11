"""An application tokenizer joins under its own id and never under a published one (R-16)."""

from __future__ import annotations

import pytest
from cwa import Snapshot, assemble

from app import context
from tests.conftest import conversation


class Chars:
    id = "chars/v1"

    def count(self, text: str) -> int:
        return len(text)


def test_an_application_tokenizer_under_its_own_id():
    document = context.snapshot(conversation("01-export"), "account-help")
    document["tokenizer"] = Chars.id
    result = assemble(Snapshot.from_json(document, tokenizers={Chars.id: Chars()}))
    assert result.trace["context"]["tokenizer"] == "chars/v1"
    estimate = assemble(Snapshot.from_json({**document, "tokenizer": "estimate-utf8/v1"}))
    assert result.trace["result"]["input_tokens"] > estimate.trace["result"]["input_tokens"] * 3


def test_a_published_id_cannot_be_overridden():
    document = context.snapshot(conversation("01-export"), "account-help")
    with pytest.raises(ValueError):
        Snapshot.from_json(document, tokenizers={"estimate-utf8/v1": Chars()})
