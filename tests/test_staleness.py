"""Tests for depwatch.staleness."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import MagicMock

import pytest

from depwatch.staleness import (
    StalenessEntry,
    StalenessReport,
    _days_since,
    evaluate_staleness,
    evaluate_all,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _iso(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _make_update(package: str, days_ago: Optional[int] = None, language: str = "python"):
    release = MagicMock()
    release.released_at = _iso(days_ago) if days_ago is not None else None
    update = MagicMock()
    update.package = package
    update.language = language
    update.current_version = "1.0.0"
    update.latest_version = "2.0.0"
    update.release = release
    return update


def _make_digest(project: str, updates):
    digest = MagicMock()
    digest.project_name = project
    digest.updates = updates
    return digest


# ---------------------------------------------------------------------------
# _days_since
# ---------------------------------------------------------------------------

def test_days_since_none_returns_zero():
    assert _days_since(None) == 0


def test_days_since_invalid_string_returns_zero():
    assert _days_since("not-a-date") == 0


def test_days_since_recent_is_zero_or_one():
    now = datetime.now(timezone.utc).isoformat()
    assert _days_since(now) in (0, 1)


def test_days_since_old_date():
    old = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    assert _days_since(old) >= 200


# ---------------------------------------------------------------------------
# StalenessReport
# ---------------------------------------------------------------------------

def test_report_is_empty_when_no_entries():
    assert StalenessReport().is_empty()


def test_report_not_empty_with_entries():
    e = StalenessEntry("p", "pkg", "python", "1", "2", 10, False)
    assert not StalenessReport(entries=[e]).is_empty()


def test_stale_only_filters_correctly():
    fresh = StalenessEntry("p", "a", "python", "1", "2", 10, False)
    stale = StalenessEntry("p", "b", "python", "1", "2", 200, True)
    report = StalenessReport(entries=[fresh, stale])
    assert report.stale_only() == [stale]


def test_to_dict_structure():
    e = StalenessEntry("proj", "pkg", "go", "v1", "v2", 5, False)
    d = StalenessReport(entries=[e]).to_dict()
    assert d["total"] == 1
    assert d["stale_count"] == 0
    assert isinstance(d["entries"], list)


# ---------------------------------------------------------------------------
# evaluate_staleness
# ---------------------------------------------------------------------------

def test_evaluate_staleness_marks_stale():
    digest = _make_digest("myproject", [_make_update("requests", days_ago=200)])
    report = evaluate_staleness(digest, stale_days=180)
    assert len(report.entries) == 1
    assert report.entries[0].stale is True


def test_evaluate_staleness_marks_fresh():
    digest = _make_digest("myproject", [_make_update("requests", days_ago=10)])
    report = evaluate_staleness(digest, stale_days=180)
    assert report.entries[0].stale is False


def test_evaluate_staleness_no_released_at():
    digest = _make_digest("myproject", [_make_update("requests", days_ago=None)])
    report = evaluate_staleness(digest, stale_days=180)
    assert report.entries[0].days_since_release == 0
    assert report.entries[0].stale is False


# ---------------------------------------------------------------------------
# evaluate_all
# ---------------------------------------------------------------------------

def test_evaluate_all_combines_digests():
    d1 = _make_digest("proj1", [_make_update("flask", 5)])
    d2 = _make_digest("proj2", [_make_update("gin", 200, language="go")])
    report = evaluate_all([d1, d2], stale_days=180)
    assert len(report.entries) == 2
    assert len(report.stale_only()) == 1


def test_evaluate_all_empty_digests():
    report = evaluate_all([])
    assert report.is_empty()
