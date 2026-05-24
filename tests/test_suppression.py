"""Tests for depwatch.suppression."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.checker import UpdateInfo
from depwatch.suppression import (
    SuppressionList,
    apply_suppression,
    load_suppression,
    save_suppression,
)


def _make_update(project: str = "myapp", package: str = "requests") -> UpdateInfo:
    return UpdateInfo(
        project=project,
        package=package,
        current="1.0.0",
        latest="2.0.0",
        language="python",
    )


# ---------------------------------------------------------------------------
# SuppressionList.is_suppressed
# ---------------------------------------------------------------------------

def test_empty_list_suppresses_nothing():
    sl = SuppressionList()
    assert not sl.is_suppressed(_make_update())


def test_exact_match_is_suppressed():
    sl = SuppressionList(entries=[{"project": "myapp", "package": "requests"}])
    assert sl.is_suppressed(_make_update("myapp", "requests"))


def test_different_package_not_suppressed():
    sl = SuppressionList(entries=[{"project": "myapp", "package": "flask"}])
    assert not sl.is_suppressed(_make_update("myapp", "requests"))


def test_wildcard_project_matches_any_project():
    sl = SuppressionList(entries=[{"project": None, "package": "requests"}])
    assert sl.is_suppressed(_make_update("proj_a", "requests"))
    assert sl.is_suppressed(_make_update("proj_b", "requests"))


def test_wildcard_package_matches_any_package():
    sl = SuppressionList(entries=[{"project": "myapp", "package": None}])
    assert sl.is_suppressed(_make_update("myapp", "requests"))
    assert sl.is_suppressed(_make_update("myapp", "flask"))


def test_empty_string_project_acts_as_wildcard():
    sl = SuppressionList(entries=[{"project": "", "package": "requests"}])
    assert sl.is_suppressed(_make_update("anything", "requests"))


# ---------------------------------------------------------------------------
# apply_suppression
# ---------------------------------------------------------------------------

def test_apply_suppression_removes_matching():
    updates = [_make_update("myapp", "requests"), _make_update("myapp", "flask")]
    sl = SuppressionList(entries=[{"project": "myapp", "package": "requests"}])
    result = apply_suppression(updates, sl)
    assert len(result) == 1
    assert result[0].package == "flask"


def test_apply_suppression_empty_list_returns_all():
    updates = [_make_update(), _make_update("myapp", "flask")]
    result = apply_suppression(updates, SuppressionList())
    assert result == updates


# ---------------------------------------------------------------------------
# load_suppression / save_suppression
# ---------------------------------------------------------------------------

def test_load_suppression_missing_file_returns_empty(tmp_path):
    sl = load_suppression(tmp_path / "nope.json")
    assert sl.entries == []


def test_load_suppression_invalid_json_returns_empty(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not-json", encoding="utf-8")
    sl = load_suppression(p)
    assert sl.entries == []


def test_load_suppression_wrong_type_returns_empty(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(["a", "b"]), encoding="utf-8")
    sl = load_suppression(p)
    assert sl.entries == []


def test_save_and_load_round_trip(tmp_path):
    p = tmp_path / "suppress.json"
    sl = SuppressionList(entries=[{"project": "myapp", "package": "requests"}])
    save_suppression(sl, p)
    loaded = load_suppression(p)
    assert loaded.entries == sl.entries


def test_save_creates_valid_json(tmp_path):
    p = tmp_path / "suppress.json"
    save_suppression(SuppressionList(entries=[{"project": None, "package": "boto3"}]), p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "suppressed" in data
    assert data["suppressed"][0]["package"] == "boto3"
