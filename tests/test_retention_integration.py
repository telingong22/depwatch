"""Integration tests: retention + history round-trip."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from depwatch.history import HistoryEntry, load_history, save_history
from depwatch.retention import RetentionPolicy, prune_history


def _entry(days_ago: float, pkg: str = "pkg") -> HistoryEntry:
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return HistoryEntry(project="proj", package=pkg, previous="1.0.0", latest="2.0.0", timestamp=ts)


def test_prune_then_reload_consistent(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [_entry(5, "a"), _entry(100, "b"), _entry(200, "c")]
    save_history(path, entries)

    pruned = prune_history(path, RetentionPolicy(max_days=60))
    assert pruned == 2

    reloaded = load_history(path)
    assert len(reloaded) == 1
    assert reloaded[0].package == "a"


def test_prune_preserves_file_as_valid_json(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [_entry(1), _entry(400)]
    save_history(path, entries)
    prune_history(path, RetentionPolicy(max_days=30))
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list)


def test_prune_all_entries_leaves_empty_file(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [_entry(500), _entry(600)]
    save_history(path, entries)
    pruned = prune_history(path, RetentionPolicy(max_days=30))
    assert pruned == 2
    reloaded = load_history(path)
    assert reloaded == []
