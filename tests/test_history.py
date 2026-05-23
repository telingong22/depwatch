"""Tests for depwatch.history."""

import json
import os
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from depwatch.history import (
    HistoryEntry,
    append_entry,
    load_history,
    record_updates,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_entry(**kwargs) -> HistoryEntry:
    defaults = dict(
        project="myapp",
        package="requests",
        language="python",
        from_version="2.28.0",
        to_version="2.31.0",
        detected_at="2024-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    return HistoryEntry(**defaults)


def _make_update(package, current, latest):
    return SimpleNamespace(package=package, current_version=current, latest_version=latest)


# ---------------------------------------------------------------------------
# HistoryEntry
# ---------------------------------------------------------------------------

def test_history_entry_round_trip():
    e = _make_entry()
    assert HistoryEntry.from_dict(e.to_dict()) == e


def test_history_entry_to_dict_keys():
    keys = set(_make_entry().to_dict().keys())
    assert keys == {"project", "package", "language", "from_version", "to_version", "detected_at"}


# ---------------------------------------------------------------------------
# load_history
# ---------------------------------------------------------------------------

def test_load_history_missing_file(tmp_path):
    result = load_history(str(tmp_path / "no_such.json"))
    assert result == []


def test_load_history_valid(tmp_path):
    p = tmp_path / "hist.json"
    entry = _make_entry()
    p.write_text(json.dumps([entry.to_dict()]), encoding="utf-8")
    loaded = load_history(str(p))
    assert len(loaded) == 1
    assert loaded[0] == entry


def test_load_history_invalid_json(tmp_path):
    p = tmp_path / "hist.json"
    p.write_text("not-json", encoding="utf-8")
    assert load_history(str(p)) == []


def test_load_history_wrong_type(tmp_path):
    p = tmp_path / "hist.json"
    p.write_text(json.dumps({"oops": True}), encoding="utf-8")
    assert load_history(str(p)) == []


# ---------------------------------------------------------------------------
# append_entry
# ---------------------------------------------------------------------------

def test_append_entry_creates_file(tmp_path):
    p = tmp_path / "sub" / "hist.json"
    append_entry(str(p), _make_entry())
    assert p.exists()


def test_append_entry_accumulates(tmp_path):
    p = tmp_path / "hist.json"
    append_entry(str(p), _make_entry(package="requests"))
    append_entry(str(p), _make_entry(package="flask"))
    loaded = load_history(str(p))
    assert len(loaded) == 2
    assert {e.package for e in loaded} == {"requests", "flask"}


# ---------------------------------------------------------------------------
# record_updates
# ---------------------------------------------------------------------------

def test_record_updates_writes_all(tmp_path):
    p = tmp_path / "hist.json"
    updates = [
        _make_update("requests", "2.28.0", "2.31.0"),
        _make_update("flask", "2.0.0", "3.0.0"),
    ]
    record_updates(str(p), "myapp", "python", updates)
    loaded = load_history(str(p))
    assert len(loaded) == 2
    assert all(e.project == "myapp" for e in loaded)
    assert all(e.language == "python" for e in loaded)


def test_record_updates_empty_list(tmp_path):
    p = tmp_path / "hist.json"
    record_updates(str(p), "myapp", "python", [])
    assert not p.exists()
