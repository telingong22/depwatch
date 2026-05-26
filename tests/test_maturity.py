"""Tests for depwatch.maturity."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from depwatch.maturity import (
    MaturityReport,
    MaturityScore,
    _age_days,
    _is_major,
    _maturity_label,
    build_maturity_report,
    score_update,
)


def _iso(days_ago: int) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _make_update(
    package: str = "requests",
    current: str = "1.0.0",
    latest: str = "1.1.0",
    published_at: str | None = None,
) -> MagicMock:
    release_info = MagicMock()
    release_info.published_at = published_at
    u = MagicMock()
    u.package_name = package
    u.current_version = current
    u.latest_version = latest
    u.release_info = release_info
    return u


def _make_digest(project: str, updates: list) -> MagicMock:
    d = MagicMock()
    d.project_name = project
    d.updates = updates
    return d


# --- _age_days ---

def test_age_days_none_returns_zero():
    assert _age_days(None) == 0


def test_age_days_invalid_returns_zero():
    assert _age_days("not-a-date") == 0


def test_age_days_recent():
    result = _age_days(_iso(3))
    assert 2 <= result <= 4


def test_age_days_old():
    result = _age_days(_iso(60))
    assert 59 <= result <= 61


# --- _maturity_label ---

def test_maturity_label_fresh():
    assert _maturity_label(3, False) == "fresh"


def test_maturity_label_recent():
    assert _maturity_label(15, False) == "recent"


def test_maturity_label_stable():
    assert _maturity_label(45, False) == "stable"


def test_maturity_label_mature():
    assert _maturity_label(100, False) == "mature"


def test_maturity_label_new_major_within_14_days():
    assert _maturity_label(10, True) == "new-major"


def test_maturity_label_major_after_14_days_uses_age():
    assert _maturity_label(20, True) == "recent"


# --- _is_major ---

def test_is_major_true():
    u = _make_update(current="1.2.3", latest="2.0.0")
    assert _is_major(u) is True


def test_is_major_false_minor():
    u = _make_update(current="1.2.3", latest="1.3.0")
    assert _is_major(u) is False


def test_is_major_with_v_prefix():
    u = _make_update(current="v1.0.0", latest="v2.0.0")
    assert _is_major(u) is True


def test_is_major_invalid_version():
    u = _make_update(current="unknown", latest="also-unknown")
    assert _is_major(u) is False


# --- score_update ---

def test_score_update_fields():
    u = _make_update(published_at=_iso(5))
    score = score_update("myproject", u)
    assert score.project == "myproject"
    assert score.package == "requests"
    assert score.latest_version == "1.1.0"
    assert score.label == "fresh"
    assert score.is_major is False


def test_score_update_to_dict_keys():
    u = _make_update()
    score = score_update("proj", u)
    d = score.to_dict()
    assert set(d.keys()) == {
        "project", "package", "latest_version", "age_days", "label", "is_major"
    }


def test_score_update_str_contains_package():
    u = _make_update(published_at=_iso(50))
    score = score_update("proj", u)
    assert "requests" in str(score)
    assert "stable" in str(score)


# --- MaturityReport ---

def test_report_is_empty_when_no_scores():
    report = MaturityReport(scores=[])
    assert report.is_empty() is True


def test_report_not_empty_with_scores():
    u = _make_update()
    score = score_update("proj", u)
    report = MaturityReport(scores=[score])
    assert report.is_empty() is False


def test_report_by_label_filters_correctly():
    u1 = _make_update(published_at=_iso(3))
    u2 = _make_update(package="flask", published_at=_iso(50))
    s1 = score_update("proj", u1)
    s2 = score_update("proj", u2)
    report = MaturityReport(scores=[s1, s2])
    fresh = report.by_label("fresh")
    assert len(fresh) == 1
    assert fresh[0].package == "requests"


# --- build_maturity_report ---

def test_build_maturity_report_aggregates_all_digests():
    u1 = _make_update(package="requests", published_at=_iso(3))
    u2 = _make_update(package="flask", published_at=_iso(60))
    d1 = _make_digest("proj-a", [u1])
    d2 = _make_digest("proj-b", [u2])
    report = build_maturity_report([d1, d2])
    assert len(report.scores) == 2


def test_build_maturity_report_empty_digests():
    report = build_maturity_report([])
    assert report.is_empty() is True


def test_build_maturity_report_sorted_by_age_ascending():
    u_old = _make_update(package="old-pkg", published_at=_iso(90))
    u_new = _make_update(package="new-pkg", published_at=_iso(2))
    d = _make_digest("proj", [u_old, u_new])
    report = build_maturity_report([d])
    assert report.scores[0].package == "new-pkg"
    assert report.scores[1].package == "old-pkg"
