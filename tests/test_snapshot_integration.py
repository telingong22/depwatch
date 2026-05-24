"""Integration tests for snapshot save/load/diff round-trip."""
from __future__ import annotations

import json

import pytest

from depwatch.snapshot import (
    Snapshot,
    SnapshotEntry,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _entry(pkg: str, ver: str) -> SnapshotEntry:
    return SnapshotEntry(package=pkg, version=ver)


def test_save_then_load_preserves_all_entries(tmp_path):
    path = str(tmp_path / "snap.json")
    snap = Snapshot(
        project="integration",
        entries=[
            _entry("requests", "2.31.0"),
            _entry("flask", "3.0.0"),
            _entry("celery", "5.3.4"),
        ],
    )
    save_snapshot(path, snap)
    loaded = load_snapshot(path)
    assert loaded is not None
    assert len(loaded.entries) == 3
    versions = {e.package: e.version for e in loaded.entries}
    assert versions["requests"] == "2.31.0"
    assert versions["celery"] == "5.3.4"


def test_snapshot_file_is_valid_json(tmp_path):
    path = str(tmp_path / "snap.json")
    save_snapshot(path, Snapshot(project="p", entries=[_entry("boto3", "1.0.0")]))
    with open(path) as fh:
        data = json.load(fh)
    assert "project" in data
    assert "entries" in data


def test_diff_after_update_cycle(tmp_path):
    path = str(tmp_path / "snap.json")

    v1 = Snapshot(
        project="app",
        entries=[_entry("django", "4.2.0"), _entry("gunicorn", "21.0.0")],
    )
    save_snapshot(path, v1)

    v2 = Snapshot(
        project="app",
        entries=[_entry("django", "5.0.0"), _entry("gunicorn", "21.0.0")],
    )

    old = load_snapshot(path)
    diff = diff_snapshots(old, v2)
    assert "django" in diff
    assert diff["django"] == ("4.2.0", "5.0.0")
    assert "gunicorn" not in diff


def test_empty_snapshot_produces_empty_diff(tmp_path):
    path = str(tmp_path / "snap.json")
    snap = Snapshot(project="empty", entries=[])
    save_snapshot(path, snap)
    loaded = load_snapshot(path)
    diff = diff_snapshots(loaded, snap)
    assert diff == {}
