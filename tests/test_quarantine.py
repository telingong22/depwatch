"""Tests for depwatch.quarantine."""
from __future__ import annotations

import json
import os
import pytest

from depwatch.checker import UpdateInfo
from depwatch.quarantine import (
    QuarantineEntry,
    _entry_key,
    list_active,
    load_quarantine,
    quarantine_update,
    release_from_quarantine,
    save_quarantine,
)


def _make_update(project="myapp", package="requests", current="2.28.0", latest="2.31.0", language="python"):
    return UpdateInfo(project=project, package=package, current=current, latest=latest, language=language)


# --- QuarantineEntry ---

def test_entry_to_dict_keys():
    e = QuarantineEntry(
        project="p", package="pkg", current="1.0", latest="2.0",
        language="python", reason="major bump"
    )
    d = e.to_dict()
    assert set(d.keys()) == {"project", "package", "current", "latest", "language", "reason", "quarantined_at", "released_at"}


def test_entry_round_trip():
    e = QuarantineEntry(
        project="p", package="pkg", current="1.0", latest="2.0",
        language="go", reason="security", quarantined_at="2024-01-01T00:00:00+00:00", released_at=None
    )
    assert QuarantineEntry.from_dict(e.to_dict()) == e


def test_entry_released_at_defaults_none():
    e = QuarantineEntry(project="p", package="x", current="1", latest="2", language="python", reason="test")
    assert e.released_at is None


# --- _entry_key ---

def test_entry_key_format():
    assert _entry_key("proj", "pkg", "1.2.3") == "proj::pkg::1.2.3"


# --- load / save ---

def test_load_quarantine_missing_file(tmp_path):
    result = load_quarantine(str(tmp_path / "q.json"))
    assert result == {}


def test_load_quarantine_invalid_json(tmp_path):
    p = tmp_path / "q.json"
    p.write_text("not json")
    assert load_quarantine(str(p)) == {}


def test_load_quarantine_wrong_type(tmp_path):
    p = tmp_path / "q.json"
    p.write_text(json.dumps([1, 2, 3]))
    assert load_quarantine(str(p)) == {}


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "q.json")
    e = QuarantineEntry(project="a", package="b", current="1", latest="2", language="python", reason="r")
    key = _entry_key("a", "b", "2")
    save_quarantine(path, {key: e})
    loaded = load_quarantine(path)
    assert key in loaded
    assert loaded[key].package == "b"


# --- quarantine_update ---

def test_quarantine_update_creates_entry(tmp_path):
    path = str(tmp_path / "q.json")
    u = _make_update()
    entry = quarantine_update(u, "needs review", path)
    assert entry.reason == "needs review"
    assert entry.released_at is None
    assert os.path.exists(path)


def test_quarantine_update_persists(tmp_path):
    path = str(tmp_path / "q.json")
    u = _make_update()
    quarantine_update(u, "test", path)
    store = load_quarantine(path)
    assert len(store) == 1


# --- release_from_quarantine ---

def test_release_sets_released_at(tmp_path):
    path = str(tmp_path / "q.json")
    u = _make_update()
    quarantine_update(u, "test", path)
    result = release_from_quarantine(u.project, u.package, u.latest, path)
    assert result is True
    store = load_quarantine(path)
    key = _entry_key(u.project, u.package, u.latest)
    assert store[key].released_at is not None


def test_release_missing_entry_returns_false(tmp_path):
    path = str(tmp_path / "q.json")
    result = release_from_quarantine("x", "y", "9.9.9", path)
    assert result is False


# --- list_active ---

def test_list_active_excludes_released(tmp_path):
    path = str(tmp_path / "q.json")
    u1 = _make_update(package="requests", latest="2.31.0")
    u2 = _make_update(package="flask", latest="3.0.0")
    quarantine_update(u1, "r1", path)
    quarantine_update(u2, "r2", path)
    release_from_quarantine(u1.project, u1.package, u1.latest, path)
    active = list_active(path)
    assert len(active) == 1
    assert active[0].package == "flask"


def test_list_active_empty_store(tmp_path):
    path = str(tmp_path / "q.json")
    assert list_active(path) == []
