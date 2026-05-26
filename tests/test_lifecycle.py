"""Unit tests for depwatch.lifecycle."""
from __future__ import annotations

import json
import os

import pytest

from depwatch.checker import UpdateInfo
from depwatch.lifecycle import (
    LifecycleEntry,
    _entry_key,
    entries_by_stage,
    load_lifecycle,
    save_lifecycle,
    upsert_entry,
)


def _make_update(pkg="requests", current="1.0.0", latest="2.0.0", project="myapp") -> UpdateInfo:
    return UpdateInfo(
        project_name=project,
        package=pkg,
        current_version=current,
        latest_version=latest,
        language="python",
    )


def test_entry_key_format():
    assert _entry_key("proj", "pkg", "1.2.3") == "proj::pkg::1.2.3"


def test_lifecycle_entry_round_trip():
    e = LifecycleEntry(
        project="p", package="q", current_version="1.0", latest_version="2.0",
        stage="new", created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-02T00:00:00+00:00", note="hi",
    )
    assert LifecycleEntry.from_dict(e.to_dict()) == e


def test_lifecycle_entry_to_dict_keys():
    e = LifecycleEntry(
        project="p", package="q", current_version="1.0", latest_version="2.0",
        stage="active", created_at="t", updated_at="t",
    )
    keys = set(e.to_dict())
    assert keys == {"project", "package", "current_version", "latest_version",
                    "stage", "created_at", "updated_at", "note"}


def test_upsert_entry_creates_new():
    store: dict = {}
    u = _make_update()
    entry = upsert_entry(store, u, stage="new")
    assert entry.stage == "new"
    assert entry.package == "requests"
    assert len(store) == 1


def test_upsert_entry_updates_existing_stage():
    store: dict = {}
    u = _make_update()
    upsert_entry(store, u, stage="new")
    upsert_entry(store, u, stage="active", note="in progress")
    assert len(store) == 1
    key = list(store.keys())[0]
    assert store[key].stage == "active"
    assert store[key].note == "in progress"


def test_upsert_entry_invalid_stage_raises():
    store: dict = {}
    u = _make_update()
    with pytest.raises(ValueError, match="Invalid stage"):
        upsert_entry(store, u, stage="unknown")


def test_entries_by_stage_filters_correctly():
    store: dict = {}
    u1 = _make_update(pkg="a", latest="2.0")
    u2 = _make_update(pkg="b", latest="3.0")
    upsert_entry(store, u1, stage="new")
    upsert_entry(store, u2, stage="resolved")
    new_entries = entries_by_stage(store, "new")
    assert len(new_entries) == 1
    assert new_entries[0].package == "a"


def test_save_and_load_lifecycle(tmp_path):
    path = str(tmp_path / "lifecycle.json")
    store: dict = {}
    u = _make_update()
    upsert_entry(store, u, stage="active")
    save_lifecycle(path, store)
    loaded = load_lifecycle(path)
    assert len(loaded) == 1
    entry = list(loaded.values())[0]
    assert entry.stage == "active"
    assert entry.package == "requests"


def test_load_lifecycle_missing_file(tmp_path):
    result = load_lifecycle(str(tmp_path / "nonexistent.json"))
    assert result == {}


def test_load_lifecycle_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not json")
    result = load_lifecycle(str(path))
    assert result == {}


def test_load_lifecycle_wrong_type(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([1, 2, 3]))
    result = load_lifecycle(str(path))
    assert result == {}
