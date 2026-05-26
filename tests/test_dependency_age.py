"""Tests for depwatch.dependency_age."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from depwatch.checker import UpdateInfo
from depwatch.dependency_age import (
    AgeEntry,
    AgeReport,
    _age_days,
    _entry_from_update,
    _parse_iso,
    build_age_report,
)
from depwatch.digest import ProjectDigest
from depwatch.fetcher import ReleaseInfo


def _iso(days_ago: int) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _make_update(
    project: str = "myproject",
    package: str = "requests",
    language: str = "python",
    current: str = "2.27.0",
    latest: str = "2.28.0",
    published_at: str | None = None,
) -> UpdateInfo:
    release = ReleaseInfo(version=latest, published_at=published_at)
    return UpdateInfo(
        project=project,
        package=package,
        language=language,
        current_version=current,
        release=release,
    )


def test_parse_iso_valid():
    result = _parse_iso("2023-06-01T12:00:00+00:00")
    assert result is not None
    assert result.year == 2023


def test_parse_iso_none_returns_none():
    assert _parse_iso(None) is None


def test_parse_iso_invalid_returns_none():
    assert _parse_iso("not-a-date") is None


def test_age_days_none_returns_zero():
    assert _age_days(None) == 0


def test_age_days_recent_is_zero_or_one():
    iso = _iso(0)
    assert _age_days(iso) <= 1


def test_age_days_old_returns_correct():
    iso = _iso(30)
    result = _age_days(iso)
    assert 29 <= result <= 31


def test_entry_from_update_fields():
    u = _make_update(published_at=_iso(10))
    entry = _entry_from_update(u)
    assert entry.project == "myproject"
    assert entry.package == "requests"
    assert entry.language == "python"
    assert entry.current_version == "2.27.0"
    assert entry.latest_version == "2.28.0"
    assert 9 <= entry.age_days <= 11


def test_age_entry_to_dict_keys():
    u = _make_update(published_at=_iso(5))
    entry = _entry_from_update(u)
    d = entry.to_dict()
    assert set(d.keys()) == {
        "project", "package", "language",
        "current_version", "latest_version",
        "published_at", "age_days",
    }


def test_age_entry_str_contains_package():
    u = _make_update(published_at=_iso(7))
    entry = _entry_from_update(u)
    assert "requests" in str(entry)
    assert "age=" in str(entry)


def test_age_report_is_empty_when_no_entries():
    report = AgeReport()
    assert report.is_empty()


def test_age_report_not_empty_with_entries():
    u = _make_update(published_at=_iso(3))
    report = AgeReport(entries=[_entry_from_update(u)])
    assert not report.is_empty()


def test_age_report_oldest_first_ordering():
    u1 = _make_update(package="old", published_at=_iso(20))
    u2 = _make_update(package="new", published_at=_iso(2))
    report = AgeReport(entries=[_entry_from_update(u1), _entry_from_update(u2)])
    ordered = report.oldest_first()
    assert ordered[0].package == "old"
    assert ordered[1].package == "new"


def test_build_age_report_from_digests():
    u = _make_update(published_at=_iso(15))
    digest = ProjectDigest(project="myproject", updates=[u])
    report = build_age_report([digest])
    assert not report.is_empty()
    assert report.entries[0].package == "requests"


def test_build_age_report_empty_digests():
    report = build_age_report([])
    assert report.is_empty()
