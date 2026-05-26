"""Tests for depwatch.anomaly."""
from __future__ import annotations

import pytest

from depwatch.anomaly import (
    AnomalyEntry,
    AnomalyReport,
    detect_anomalies,
    _count_per_package,
)
from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


def _make_update(package: str, language: str = "python") -> UpdateInfo:
    return UpdateInfo(
        project="myproject",
        package=package,
        language=language,
        current="1.0.0",
        latest="1.1.0",
        published_at=None,
    )


def _make_digest(updates: list, project: str = "myproject") -> ProjectDigest:
    return ProjectDigest(project=project, updates=updates)


# ---------------------------------------------------------------------------
# AnomalyEntry
# ---------------------------------------------------------------------------

def test_anomaly_entry_to_dict_keys():
    entry = AnomalyEntry(
        project="p", package="requests", language="python",
        update_count=5, threshold=3,
    )
    d = entry.to_dict()
    assert set(d.keys()) == {"project", "package", "language", "update_count", "threshold"}


def test_anomaly_entry_str_contains_package():
    entry = AnomalyEntry(
        project="p", package="requests", language="python",
        update_count=5, threshold=3,
    )
    assert "requests" in str(entry)
    assert "5" in str(entry)
    assert "3" in str(entry)


# ---------------------------------------------------------------------------
# AnomalyReport
# ---------------------------------------------------------------------------

def test_anomaly_report_is_empty_when_no_entries():
    assert AnomalyReport().is_empty()


def test_anomaly_report_not_empty_with_entries():
    entry = AnomalyEntry(
        project="p", package="pkg", language="go",
        update_count=4, threshold=3,
    )
    report = AnomalyReport(entries=[entry])
    assert not report.is_empty()


def test_anomaly_report_to_dict_has_anomalies_key():
    report = AnomalyReport()
    assert "anomalies" in report.to_dict()


# ---------------------------------------------------------------------------
# _count_per_package
# ---------------------------------------------------------------------------

def test_count_per_package_single():
    updates = [_make_update("requests")]
    assert _count_per_package(updates) == {"requests": 1}


def test_count_per_package_multiple_same():
    updates = [_make_update("requests")] * 4
    assert _count_per_package(updates) == {"requests": 4}


def test_count_per_package_mixed():
    updates = [
        _make_update("requests"),
        _make_update("flask"),
        _make_update("requests"),
    ]
    counts = _count_per_package(updates)
    assert counts["requests"] == 2
    assert counts["flask"] == 1


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

def test_detect_anomalies_no_anomalies_below_threshold():
    updates = [_make_update("requests")] * 3  # equal to default threshold, not above
    digest = _make_digest(updates)
    report = detect_anomalies([digest], threshold=3)
    assert report.is_empty()


def test_detect_anomalies_flags_above_threshold():
    updates = [_make_update("requests")] * 4
    digest = _make_digest(updates)
    report = detect_anomalies([digest], threshold=3)
    assert not report.is_empty()
    assert report.entries[0].package == "requests"
    assert report.entries[0].update_count == 4


def test_detect_anomalies_multiple_projects():
    d1 = _make_digest([_make_update("flask")] * 5, project="proj1")
    d2 = _make_digest([_make_update("gin", language="go")] * 2, project="proj2")
    report = detect_anomalies([d1, d2], threshold=3)
    assert len(report.entries) == 1
    assert report.entries[0].project == "proj1"


def test_detect_anomalies_empty_digests():
    report = detect_anomalies([])
    assert report.is_empty()


def test_detect_anomalies_invalid_threshold():
    with pytest.raises(ValueError):
        detect_anomalies([], threshold=0)
