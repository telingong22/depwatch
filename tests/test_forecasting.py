"""Tests for depwatch.forecasting."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from depwatch.forecasting import (
    ForecastEntry,
    ForecastReport,
    _forecast_entry,
    _parse_iso,
    build_forecast,
)
from depwatch.history import HistoryEntry


def _dt(days_ago: int) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(days=days_ago)


def _iso(days_ago: int) -> str:
    return _dt(days_ago).isoformat()


def _make_entry(project: str, package: str, language: str, days_ago: int) -> HistoryEntry:
    return HistoryEntry(
        project=project,
        package=package,
        language=language,
        current_version="1.0.0",
        latest_version="1.1.0",
        detected_at=_iso(days_ago),
    )


# --- _parse_iso ---

def test_parse_iso_valid():
    iso = "2024-01-15T12:00:00+00:00"
    result = _parse_iso(iso)
    assert result is not None
    assert result.year == 2024


def test_parse_iso_none_returns_none():
    assert _parse_iso(None) is None


def test_parse_iso_invalid_returns_none():
    assert _parse_iso("not-a-date") is None


# --- _forecast_entry ---

def test_forecast_entry_single_timestamp_no_avg():
    ts = [_dt(5)]
    entry = _forecast_entry("proj", "pkg", "python", ts)
    assert entry.avg_days_between_releases == 0.0
    assert entry.next_expected_at is None


def test_forecast_entry_two_timestamps_computes_avg():
    ts = [_dt(20), _dt(10)]
    entry = _forecast_entry("proj", "pkg", "python", ts)
    assert 9.0 <= entry.avg_days_between_releases <= 11.0
    assert entry.next_expected_at is not None


def test_forecast_entry_next_expected_after_last():
    ts = [_dt(30), _dt(20), _dt(10)]
    entry = _forecast_entry("proj", "pkg", "python", ts)
    last = datetime.fromisoformat(entry.last_released_at)
    nxt = datetime.fromisoformat(entry.next_expected_at)
    assert nxt > last


def test_forecast_entry_empty_timestamps():
    entry = _forecast_entry("proj", "pkg", "go", [])
    assert entry.avg_days_between_releases == 0.0
    assert entry.last_released_at is None
    assert entry.next_expected_at is None


# --- ForecastEntry.to_dict ---

def test_forecast_entry_to_dict_keys():
    entry = ForecastEntry(
        project="p", package="q", language="python",
        avg_days_between_releases=7.5,
        last_released_at="2024-01-01T00:00:00+00:00",
        next_expected_at="2024-01-08T00:00:00+00:00",
    )
    d = entry.to_dict()
    assert set(d.keys()) == {
        "project", "package", "language",
        "avg_days_between_releases", "last_released_at", "next_expected_at",
    }


def test_forecast_entry_str_contains_package():
    entry = ForecastEntry(
        project="p", package="requests", language="python",
        avg_days_between_releases=14.0,
        last_released_at=None,
        next_expected_at=None,
    )
    assert "requests" in str(entry)
    assert "14.0d" in str(entry)


# --- ForecastReport ---

def test_forecast_report_is_empty_when_no_entries():
    report = ForecastReport()
    assert report.is_empty()


def test_forecast_report_not_empty_with_entries():
    e = ForecastEntry("p", "q", "go", 7.0, None, None)
    report = ForecastReport(entries=[e])
    assert not report.is_empty()


# --- build_forecast ---

def test_build_forecast_groups_by_package():
    history = [
        _make_entry("proj", "requests", "python", 30),
        _make_entry("proj", "requests", "python", 15),
        _make_entry("proj", "requests", "python", 0),
    ]
    report = build_forecast(history)
    assert len(report.entries) == 1
    assert report.entries[0].package == "requests"
    assert report.entries[0].avg_days_between_releases > 0


def test_build_forecast_multiple_packages():
    history = [
        _make_entry("proj", "flask", "python", 20),
        _make_entry("proj", "flask", "python", 10),
        _make_entry("proj", "gin", "go", 25),
        _make_entry("proj", "gin", "go", 5),
    ]
    report = build_forecast(history)
    packages = {e.package for e in report.entries}
    assert packages == {"flask", "gin"}


def test_build_forecast_empty_history():
    report = build_forecast([])
    assert report.is_empty()


def test_build_forecast_skips_invalid_detected_at():
    entry = HistoryEntry(
        project="p", package="pkg", language="python",
        current_version="1.0", latest_version="2.0",
        detected_at="bad-date",
    )
    report = build_forecast([entry])
    assert report.is_empty()
