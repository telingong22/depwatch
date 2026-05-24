"""Unit tests for depwatch.snapshot."""
from __future__ import annotations

import json
import os

import pytest

from depwatch.snapshot import (
    Snapshot,
    SnapshotEntry,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_entry(package: str, version: str) -> SnapshotEntry:
    return SnapshotEntry(package=package, version=version, captured_at="2024-01-01T00:00:00+00:00")


def test_snapshot_entry_round_trip():
    e = _make_entry("requests", "2.31.0")
    assert SnapshotEntry.from_dict(e.to_dict()) == e


def test_snapshot_entry_to_dict_keys():
    e = _make_entry("flask", "3.0.0")
    d = e.to_dict()
    assert set(d.keys()) == {"package", "version", "captured_at"}


def test_snapshot_round_trip():
    snap = Snapshot(
        project="myproject",
        entries=[_make_entry("numpy", "1.26.0"), _make_entry("pandas", "2.2.0")],
    )
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.project == snap.project
    assert len(restored.entries) == 2


def test_load_snapshot_missing_file(tmp_path):
    result = load_snapshot(str(tmp_path / "nope.json"))
    assert result is None


def test_load_snapshot_invalid_json(tmp_path):
    p = tmp_path / "snap.json"
    p.write_text("not json")
    assert load_snapshot(str(p)) is None


def test_load_snapshot_wrong_type(tmp_path):
    p = tmp_path / "snap.json"
    p.write_text(json.dumps([1, 2, 3]))
    assert load_snapshot(str(p)) is None


def test_save_and_load_snapshot(tmp_path):
    snap = Snapshot(
        project="proj",
        entries=[_make_entry("boto3", "1.34.0")],
    )
    path = str(tmp_path / "snap.json")
    save_snapshot(path, snap)
    loaded = load_snapshot(path)
    assert loaded is not None
    assert loaded.project == "proj"
    assert loaded.entries[0].package == "boto3"


def test_save_snapshot_creates_parent_dirs(tmp_path):
    path = str(tmp_path / "sub" / "dir" / "snap.json")
    save_snapshot(path, Snapshot(project="p", entries=[]))
    assert os.path.exists(path)


def test_diff_snapshots_detects_change():
    old = Snapshot(project="p", entries=[_make_entry("requests", "2.28.0")])
    new = Snapshot(project="p", entries=[_make_entry("requests", "2.31.0")])
    diff = diff_snapshots(old, new)
    assert "requests" in diff
    assert diff["requests"] == ("2.28.0", "2.31.0")


def test_diff_snapshots_no_change():
    old = Snapshot(project="p", entries=[_make_entry("flask", "3.0.0")])
    new = Snapshot(project="p", entries=[_make_entry("flask", "3.0.0")])
    assert diff_snapshots(old, new) == {}


def test_diff_snapshots_new_package():
    old = Snapshot(project="p", entries=[])
    new = Snapshot(project="p", entries=[_make_entry("django", "5.0.0")])
    diff = diff_snapshots(old, new)
    assert diff["django"] == (None, "5.0.0")


def test_diff_snapshots_no_old():
    new = Snapshot(project="p", entries=[_make_entry("celery", "5.3.0")])
    diff = diff_snapshots(None, new)
    assert diff["celery"] == (None, "5.3.0")
