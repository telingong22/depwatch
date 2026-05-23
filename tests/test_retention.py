"""Unit tests for depwatch.retention."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from depwatch.history import HistoryEntry
from depwatch.retention import RetentionPolicy, apply_retention, prune_history


def _entry(days_ago: float, package: str = "pkg") -> HistoryEntry:
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return HistoryEntry(project="proj", package=package, previous="1.0.0", latest="1.1.0", timestamp=ts)


# ---------------------------------------------------------------------------
# RetentionPolicy
# ---------------------------------------------------------------------------

def test_policy_default_max_days():
    p = RetentionPolicy()
    assert p.max_days == 90


def test_policy_invalid_max_days():
    with pytest.raises(ValueError):
        RetentionPolicy(max_days=0)


# ---------------------------------------------------------------------------
# apply_retention
# ---------------------------------------------------------------------------

def test_apply_retention_keeps_recent():
    entries = [_entry(1), _entry(10), _entry(30)]
    kept = apply_retention(entries, RetentionPolicy(max_days=60))
    assert len(kept) == 3


def test_apply_retention_drops_old():
    entries = [_entry(1), _entry(100)]
    kept = apply_retention(entries, RetentionPolicy(max_days=60))
    assert len(kept) == 1
    assert kept[0] is entries[0]


def test_apply_retention_empty_list():
    assert apply_retention([], RetentionPolicy()) == []


def test_apply_retention_all_stale():
    entries = [_entry(200), _entry(365)]
    assert apply_retention(entries, RetentionPolicy(max_days=30)) == []


# ---------------------------------------------------------------------------
# prune_history
# ---------------------------------------------------------------------------

def test_prune_history_removes_old_entries(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [_entry(1), _entry(200)]
    raw = [e.to_dict() for e in entries]
    with open(path, "w") as f:
        json.dump(raw, f)

    pruned = prune_history(path, RetentionPolicy(max_days=60))
    assert pruned == 1

    with open(path) as f:
        data = json.load(f)
    assert len(data) == 1


def test_prune_history_no_stale_entries(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [_entry(5), _entry(10)]
    raw = [e.to_dict() for e in entries]
    with open(path, "w") as f:
        json.dump(raw, f)

    pruned = prune_history(path, RetentionPolicy(max_days=30))
    assert pruned == 0


def test_prune_history_missing_file(tmp_path):
    path = str(tmp_path / "missing.json")
    # load_history returns [] for missing file; nothing to prune
    pruned = prune_history(path, RetentionPolicy(max_days=30))
    assert pruned == 0
