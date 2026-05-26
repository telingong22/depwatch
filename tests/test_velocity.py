"""Tests for depwatch.velocity."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from depwatch.velocity import (
    VelocityEntry,
    VelocityReport,
    _days_since,
    build_velocity,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_update(package: str = "requests", project: str = "myapp", language: str = "python"):
    u = MagicMock()
    u.package_name = package
    u.project_name = project
    u.language = language
    u.published_at = None
    return u


def _make_digest(updates):
    d = MagicMock()
    d.updates = updates
    return d


# ---------------------------------------------------------------------------
# VelocityEntry
# ---------------------------------------------------------------------------

def test_velocity_entry_to_dict_keys():
    e = VelocityEntry("pkg", "proj", "python", 5, 10, 0.5)
    d = e.to_dict()
    assert set(d.keys()) == {"package", "project", "language", "update_count", "days_tracked", "updates_per_day"}


def test_velocity_entry_to_dict_values():
    e = VelocityEntry("pkg", "proj", "python", 5, 10, 0.5)
    d = e.to_dict()
    assert d["update_count"] == 5
    assert d["days_tracked"] == 10
    assert d["updates_per_day"] == 0.5


def test_velocity_entry_str_contains_package():
    e = VelocityEntry("mypkg", "proj", "go", 3, 6, 0.5)
    assert "mypkg" in str(e)


# ---------------------------------------------------------------------------
# VelocityReport
# ---------------------------------------------------------------------------

def test_velocity_report_is_empty_when_no_entries():
    r = VelocityReport()
    assert r.is_empty()


def test_velocity_report_not_empty_with_entries():
    e = VelocityEntry("pkg", "proj", "python", 1, 1, 1.0)
    r = VelocityReport(entries=[e])
    assert not r.is_empty()


def test_velocity_report_fastest_sorted_descending():
    entries = [
        VelocityEntry("a", "p", "python", 1, 10, 0.1),
        VelocityEntry("b", "p", "python", 5, 2, 2.5),
        VelocityEntry("c", "p", "python", 3, 3, 1.0),
    ]
    r = VelocityReport(entries=entries)
    fastest = r.fastest(2)
    assert len(fastest) == 2
    assert fastest[0].package == "b"
    assert fastest[1].package == "c"


def test_velocity_report_to_dict_has_entries_and_fastest():
    e = VelocityEntry("pkg", "proj", "python", 2, 4, 0.5)
    r = VelocityReport(entries=[e])
    d = r.to_dict()
    assert "entries" in d
    assert "fastest" in d


# ---------------------------------------------------------------------------
# _days_since
# ---------------------------------------------------------------------------

def test_days_since_none_returns_one():
    now = datetime.utcnow()
    assert _days_since(None, now) == 1


def test_days_since_invalid_string_returns_one():
    now = datetime.utcnow()
    assert _days_since("not-a-date", now) == 1


def test_days_since_calculates_correctly():
    now = datetime(2024, 6, 15, tzinfo=timezone.utc).replace(tzinfo=None)
    past = datetime(2024, 6, 5, tzinfo=timezone.utc)
    iso = past.isoformat()
    assert _days_since(iso, now) == 10


# ---------------------------------------------------------------------------
# build_velocity
# ---------------------------------------------------------------------------

def test_build_velocity_empty_digests():
    report = build_velocity([])
    assert report.is_empty()


def test_build_velocity_single_update():
    u = _make_update()
    d = _make_digest([u])
    report = build_velocity([d])
    assert len(report.entries) == 1
    assert report.entries[0].package == "requests"


def test_build_velocity_uses_history_counts():
    u = _make_update("django", "webapp")
    d = _make_digest([u])
    counts = {"webapp:django": 20}
    report = build_velocity([d], history_counts=counts)
    assert report.entries[0].update_count == 20


def test_build_velocity_rate_is_count_over_days():
    u = _make_update("flask", "api")
    now = datetime(2024, 6, 15, tzinfo=timezone.utc).replace(tzinfo=None)
    past = datetime(2024, 6, 5, tzinfo=timezone.utc)
    u.published_at = past.isoformat()
    d = _make_digest([u])
    counts = {"api:flask": 10}
    report = build_velocity([d], history_counts=counts, now=now)
    assert report.entries[0].updates_per_day == pytest.approx(1.0)
