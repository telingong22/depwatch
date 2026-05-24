"""Unit tests for depwatch.baseline."""

from __future__ import annotations

import json
import os

import pytest

from depwatch.baseline import (
    BaselineEntry,
    diff_baseline,
    load_baseline,
    save_baseline,
)


def _entry(pkg: str, ver: str, proj: str = "myapp") -> BaselineEntry:
    return BaselineEntry(package=pkg, version=ver, project=proj, recorded_at="2024-01-01T00:00:00+00:00")


def test_baseline_entry_round_trip():
    e = _entry("requests", "2.31.0")
    assert BaselineEntry.from_dict(e.to_dict()) == e


def test_baseline_entry_to_dict_keys():
    e = _entry("flask", "3.0.0")
    d = e.to_dict()
    assert set(d.keys()) == {"package", "version", "project", "recorded_at"}


def test_load_baseline_missing_file(tmp_path):
    result = load_baseline(str(tmp_path / "nope.json"))
    assert result == []


def test_load_baseline_invalid_json(tmp_path):
    p = tmp_path / "baseline.json"
    p.write_text("not json")
    assert load_baseline(str(p)) == []


def test_load_baseline_wrong_type(tmp_path):
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps({"key": "val"}))
    assert load_baseline(str(p)) == []


def test_save_then_load_round_trip(tmp_path):
    entries = [_entry("requests", "2.31.0"), _entry("flask", "3.0.0", "api")]
    path = str(tmp_path / "baseline.json")
    save_baseline(path, entries)
    loaded = load_baseline(path)
    assert loaded == entries


def test_save_creates_valid_json(tmp_path):
    entries = [_entry("httpx", "0.27.0")]
    path = str(tmp_path / "baseline.json")
    save_baseline(path, entries)
    with open(path) as fh:
        data = json.load(fh)
    assert isinstance(data, list)
    assert data[0]["package"] == "httpx"


def test_diff_baseline_detects_version_change():
    old = [_entry("requests", "2.28.0")]
    new = [_entry("requests", "2.31.0")]
    changed = diff_baseline(old, new)
    assert "myapp/requests" in changed
    assert changed["myapp/requests"] == {"old": "2.28.0", "new": "2.31.0"}


def test_diff_baseline_no_change():
    entries = [_entry("flask", "3.0.0")]
    assert diff_baseline(entries, entries) == {}


def test_diff_baseline_new_package():
    old: list[BaselineEntry] = []
    new = [_entry("boto3", "1.34.0")]
    changed = diff_baseline(old, new)
    assert "myapp/boto3" in changed
    assert changed["myapp/boto3"]["old"] is None


def test_diff_baseline_removed_package():
    old = [_entry("deprecated-lib", "1.0.0")]
    new: list[BaselineEntry] = []
    changed = diff_baseline(old, new)
    assert "myapp/deprecated-lib" in changed
    assert changed["myapp/deprecated-lib"]["new"] is None
