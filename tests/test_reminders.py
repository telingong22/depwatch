"""Tests for depwatch.reminders and depwatch.cli_reminders."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from depwatch.reminders import (
    ReminderEntry,
    get_overdue,
    load_reminders,
    record_reminders,
    save_reminders,
    _reminder_key,
)
from depwatch.checker import UpdateInfo


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_update(project="myapp", package="requests", language="python",
                 current="2.28.0", latest="2.29.0") -> UpdateInfo:
    return UpdateInfo(project=project, package=package, language=language,
                      current=current, latest=latest)


def _entry(days_ago: int = 0, reminder_days: int = 7) -> ReminderEntry:
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return ReminderEntry(
        project="myapp", package="requests", language="python",
        latest="2.29.0", first_seen=ts, reminder_days=reminder_days,
    )


# ── ReminderEntry ─────────────────────────────────────────────────────────────

def test_entry_round_trip():
    e = _entry(days_ago=3)
    assert ReminderEntry.from_dict(e.to_dict()).latest == e.latest


def test_entry_to_dict_keys():
    keys = set(_entry().to_dict())
    assert keys == {"project", "package", "language", "latest", "first_seen", "reminder_days"}


def test_is_overdue_false_when_recent():
    assert not _entry(days_ago=2, reminder_days=7).is_overdue()


def test_is_overdue_true_when_old():
    assert _entry(days_ago=10, reminder_days=7).is_overdue()


def test_is_overdue_boundary_equal():
    assert _entry(days_ago=7, reminder_days=7).is_overdue()


def test_is_overdue_invalid_timestamp():
    e = _entry()
    e.first_seen = "not-a-date"
    assert not e.is_overdue()


# ── load / save ───────────────────────────────────────────────────────────────

def test_load_missing_file(tmp_path):
    assert load_reminders(tmp_path / "missing.json") == {}


def test_load_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    assert load_reminders(p) == {}


def test_load_wrong_type(tmp_path):
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps([1, 2, 3]))
    assert load_reminders(p) == {}


def test_save_then_load(tmp_path):
    p = tmp_path / "rem.json"
    e = _entry(days_ago=1)
    key = _reminder_key(e.project, e.package)
    save_reminders(p, {key: e})
    loaded = load_reminders(p)
    assert key in loaded
    assert loaded[key].latest == e.latest


# ── record_reminders ──────────────────────────────────────────────────────────

def test_record_creates_entry(tmp_path):
    p = tmp_path / "rem.json"
    u = _make_update()
    store = record_reminders(p, [u])
    assert _reminder_key(u.project, u.package) in store


def test_record_does_not_overwrite_same_latest(tmp_path):
    p = tmp_path / "rem.json"
    u = _make_update()
    now_old = datetime.now(timezone.utc) - timedelta(days=5)
    store1 = record_reminders(p, [u], now=now_old)
    old_seen = store1[_reminder_key(u.project, u.package)].first_seen
    store2 = record_reminders(p, [u])
    assert store2[_reminder_key(u.project, u.package)].first_seen == old_seen


def test_record_resets_on_new_latest(tmp_path):
    p = tmp_path / "rem.json"
    u1 = _make_update(latest="2.29.0")
    u2 = _make_update(latest="2.30.0")
    now_old = datetime.now(timezone.utc) - timedelta(days=5)
    record_reminders(p, [u1], now=now_old)
    store = record_reminders(p, [u2])
    entry = store[_reminder_key(u2.project, u2.package)]
    assert entry.latest == "2.30.0"
    # first_seen should be recent (within last few seconds)
    seen = datetime.fromisoformat(entry.first_seen)
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    assert (datetime.now(timezone.utc) - seen).total_seconds() < 5


# ── get_overdue ───────────────────────────────────────────────────────────────

def test_get_overdue_returns_only_overdue():
    store = {
        "a": _entry(days_ago=10, reminder_days=7),
        "b": _entry(days_ago=2, reminder_days=7),
    }
    overdue = get_overdue(store)
    assert len(overdue) == 1
    assert overdue[0].package == "requests"


def test_get_overdue_empty_store():
    assert get_overdue({}) == []
