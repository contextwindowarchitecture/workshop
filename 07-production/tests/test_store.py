"""Lab A: the store keeps every inference, replays it, and re-decides it under a candidate."""

from __future__ import annotations

import json

import store

CANDIDATES = store.HERE / "policy" / "candidates"


def test_save_replay_and_show(tmp_path, status_record):
    db = store.connect(tmp_path / "s.sqlite")
    store.save(db, "run_a", status_record)
    assert [r["run_id"] for r in store.runs(db)] == ["run_a"]
    replayed = store.replay(db, "run_a")
    assert len(replayed) == 3 and all(r.same for r in replayed)
    import io
    out = io.StringIO()
    store.show(db, "run_a", out)
    assert "obs:1: superseded" in out.getvalue() and "answer:" in out.getvalue()


def test_snapshots_are_stored_once_by_digest(tmp_path, status_record):
    db = store.connect(tmp_path / "s.sqlite")
    store.save(db, "run_a", status_record)
    store.save(db, "run_b", status_record)
    assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 3
    assert db.execute("SELECT COUNT(*) FROM inferences").fetchone()[0] == 6


def test_whatif_shows_what_a_candidate_would_change(tmp_path, status_record):
    db = store.connect(tmp_path / "s.sqlite")
    store.save(db, "run_a", status_record)
    policy = json.loads((CANDIDATES / "no-supersede" / "route-policy.json").read_text())
    profile = json.loads((CANDIDATES / "no-supersede" / "profile.json").read_text())
    total, differences = store.whatif(db, policy, profile)
    assert total == 3 and len(differences) == 1
    assert differences[0].changes["obs:1"] == ("excluded:superseded", "included")
    total, differences = store.whatif(db, json.loads((CANDIDATES / "history-tight" / "route-policy.json").read_text()),
                                      json.loads((CANDIDATES / "history-tight" / "profile.json").read_text()))
    assert differences == [], "no history in a one-question run, so a tighter cap changes nothing"
    assert db.execute("SELECT COUNT(*) FROM inferences").fetchone()[0] == 3, "what-if stores nothing"
