"""Tests for depwatch.snoozin."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.checker import UpdateInfo
from depwatch.snoozin import (
    SnoozeEntry,
    _snooze_key,
    add_snooze,
    apply_snoozes,
    load_snoozes,
    save_snoozes,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_FUTURE = (_NOW + timedelta(days=7)).isoformat()
_PAST = (_NOW - timedelta(days=1)).isoformat()


def _make_update(project: str = "myapp", package: str = "requests") -> UpdateInfo:
    return UpdateInfo(
        project_name=project,
        package_name=package,
        current_version="2.0.0",
        latest_version="3.0.0",
        language="python",
    )


# ---------------------------------------------------------------------------
# SnoozeEntry
# ---------------------------------------------------------------------------

def test_snooze_entry_to_dict_keys():
    e = SnoozeEntry(project="p", package="q", until=_FUTURE, reason="waiting")
    assert set(e.to_dict().keys()) == {"project", "package", "until", "reason"}


def test_snooze_entry_round_trip():
    e = SnoozeEntry(project="p", package="q", until=_FUTURE, reason="ci")
    assert SnoozeEntry.from_dict(e.to_dict()) == e


def test_snooze_entry_is_active_future(tmp_path):
    e = SnoozeEntry(project="p", package="q", until=_FUTURE)
    assert e.is_active(now=_NOW) is True


def test_snooze_entry_is_active_past():
    e = SnoozeEntry(project="p", package="q", until=_PAST)
    assert e.is_active(now=_NOW) is False


def test_snooze_entry_is_active_invalid_date():
    e = SnoozeEntry(project="p", package="q", until="not-a-date")
    assert e.is_active(now=_NOW) is False


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_snoozes_missing_file(tmp_path):
    result = load_snoozes(tmp_path / "nope.json")
    assert result == {}


def test_load_snoozes_invalid_json(tmp_path):
    p = tmp_path / "snooze.json"
    p.write_text("not json")
    assert load_snoozes(p) == {}


def test_save_then_load_round_trip(tmp_path):
    p = tmp_path / "snooze.json"
    entry = SnoozeEntry(project="app", package="flask", until=_FUTURE, reason="test")
    snoozes = {_snooze_key("app", "flask"): entry}
    save_snoozes(snoozes, p)
    loaded = load_snoozes(p)
    assert loaded[_snooze_key("app", "flask")] == entry


def test_save_creates_valid_json(tmp_path):
    p = tmp_path / "snooze.json"
    entry = SnoozeEntry(project="x", package="y", until=_FUTURE)
    save_snoozes({"x::y": entry}, p)
    data = json.loads(p.read_text())
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# add_snooze
# ---------------------------------------------------------------------------

def test_add_snooze_persists(tmp_path):
    p = tmp_path / "snooze.json"
    add_snooze("proj", "pkg", _FUTURE, reason="blocked", path=p)
    loaded = load_snoozes(p)
    assert _snooze_key("proj", "pkg") in loaded


# ---------------------------------------------------------------------------
# apply_snoozes
# ---------------------------------------------------------------------------

def test_apply_snoozes_removes_active(tmp_path):
    p = tmp_path / "snooze.json"
    add_snooze("myapp", "requests", _FUTURE, path=p)
    updates = [_make_update()]
    result = apply_snoozes(updates, path=p, now=_NOW)
    assert result == []


def test_apply_snoozes_keeps_expired(tmp_path):
    p = tmp_path / "snooze.json"
    add_snooze("myapp", "requests", _PAST, path=p)
    updates = [_make_update()]
    result = apply_snoozes(updates, path=p, now=_NOW)
    assert len(result) == 1


def test_apply_snoozes_keeps_unsnoozed(tmp_path):
    p = tmp_path / "snooze.json"
    add_snooze("myapp", "flask", _FUTURE, path=p)
    updates = [_make_update(package="requests")]
    result = apply_snoozes(updates, path=p, now=_NOW)
    assert len(result) == 1


def test_apply_snoozes_empty_updates(tmp_path):
    p = tmp_path / "snooze.json"
    result = apply_snoozes([], path=p, now=_NOW)
    assert result == []
