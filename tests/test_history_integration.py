"""Integration test: runner records history after a cycle."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from depwatch.history import load_history, record_updates


def _make_update(package, current, latest):
    return SimpleNamespace(package=package, current_version=current, latest_version=latest)


def test_record_then_load_round_trip(tmp_path):
    hist_path = str(tmp_path / "history.json")
    updates = [
        _make_update("requests", "2.28.0", "2.31.0"),
        _make_update("flask", None, "3.0.0"),
    ]
    record_updates(hist_path, "proj_a", "python", updates)
    record_updates(hist_path, "proj_b", "go", [_make_update("gin", "1.8.0", "1.9.1")])

    entries = load_history(hist_path)
    assert len(entries) == 3

    projects = {e.project for e in entries}
    assert projects == {"proj_a", "proj_b"}

    gin_entry = next(e for e in entries if e.package == "gin")
    assert gin_entry.language == "go"
    assert gin_entry.from_version == "1.8.0"
    assert gin_entry.to_version == "1.9.1"


def test_history_file_is_valid_json(tmp_path):
    hist_path = str(tmp_path / "history.json")
    record_updates(hist_path, "p", "python", [_make_update("django", "4.0", "5.0")])
    with open(hist_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, list)
    assert data[0]["package"] == "django"


def test_no_file_created_for_empty_updates(tmp_path):
    hist_path = str(tmp_path / "history.json")
    record_updates(hist_path, "p", "python", [])
    assert not (tmp_path / "history.json").exists()
