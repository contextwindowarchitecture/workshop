from __future__ import annotations

import json

import pytest

import common
import frameworks
import seam_impl


@pytest.fixture
def which():
    return seam_impl.name()


SENT = [n for n in common.scenario_names() if common.assemble_context(common.scenario(n))[1].payload is not None]
REFUSED = [n for n in common.scenario_names() if n not in SENT]


@pytest.mark.parametrize("seam", list(frameworks.SEAMS))
@pytest.mark.parametrize("name", SENT)
def test_the_framework_hands_the_model_exactly_the_payload(name, seam, which):
    request = common.scenario(name)
    _, result = common.assemble_context(request)
    expected = frameworks.expected_for(seam, common.texts_of(result.payload))
    received = frameworks.SEAMS[seam](request, which)
    assert received is not None
    assert received["system"] == expected["system"]
    assert received["user"] == expected["user"]


@pytest.mark.parametrize("seam", list(frameworks.SEAMS))
@pytest.mark.parametrize("name", REFUSED)
def test_a_refusal_starts_no_run_and_calls_no_model(name, seam, which):
    assert REFUSED, "W3a commits a refused scenario"
    assert frameworks.SEAMS[seam](common.scenario(name), which) is None


def test_the_agents_instructions_never_reach_the_model(which):
    received = frameworks.run_agents_sdk(common.scenario(SENT[0]), which)
    assert all("MUST NEVER REACH" not in s for s in received["system"])


def test_the_claude_agent_options_add_only_the_separator(which):
    seams = seam_impl.seams(which)
    _, result = common.assemble_context(common.scenario(SENT[0]))
    options = seams.claude_agent_options(result.payload, common.reserved_output())
    texts = common.texts_of(result.payload)
    assert options["system_prompt"] == options["separator"].join(texts["system"])
    assert options["prompt"] == texts["user"]
    assert options["allowed_tools"] == []


def test_the_committed_proof_is_current():
    import scenarios

    assert scenarios.stale("proof") == []
