from __future__ import annotations

import scenarios


def test_the_committed_suite_is_what_the_reference_builds_now():
    assert scenarios.stale("scripted-01") == [], "run `uv run scenarios.py --write`, then review the diff"
