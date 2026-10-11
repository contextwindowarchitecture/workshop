from __future__ import annotations

import invariants


def test_every_committed_snapshot_in_the_repository_holds_the_invariants():
    failures = []
    total = 0
    for workshop, label, doc, recorded in invariants.snapshots():
        total += 1
        r = invariants.check(doc, recorded)
        if not r["replays"] or not r["schema"] or r["recorded"] is False or r["problem"]:
            failures.append((label, r))
    assert total > 80, f"the walker should find every workshop's snapshots, found {total}"
    assert failures == []
