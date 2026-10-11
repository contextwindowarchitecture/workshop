"""Lab D: five items wrong in exactly one way, each earning exactly the code it names."""

from __future__ import annotations

import copy

import pytest

import impl
from tests.conftest import assembled, codes


@pytest.fixture
def negative(which):
    return impl.module("negative", which)


@pytest.mark.parametrize("name", ["claims_protected", "wrong_slot", "unmarked", "reused_id", "no_relevance"])
def test_the_item_earns_exactly_its_code(ada, baseline, negative, name):
    expected, _rule = negative.EXPECTED[name]
    bad = getattr(negative, name)()
    batches = copy.deepcopy(baseline)
    search = next(b for b in batches if b["producer"]["id"] == "help-center-search")
    search["items"].append(bad)
    _, result = assembled(ada, batches)
    assert not result.refused, "a wrong item is excluded; it should never refuse the whole assembly"
    got = codes(result.trace, "assembler")
    assert got.get(bad["id"]) == expected, got
    # Nothing else changed: the only other assembler-stage exclusions are the ones the valid snapshot already had,
    # plus, for the reused id, the twin that now shares it (R-2 excludes both).
    allowed = {"below_threshold", "duplicate_content", "source_diversity_cap"} | ({"duplicate_item_id"} if name == "reused_id" else set())
    others = {k: v for k, v in got.items() if k != bad["id"]}
    assert set(others.values()) <= allowed, others
