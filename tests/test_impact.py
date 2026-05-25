"""Tests for depwatch.impact."""
from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.impact import (
    ImpactEntry,
    ImpactReport,
    build_impact_report,
)


def _make_update(package: str, current: str, latest: str, project: str = "proj") -> UpdateInfo:
    return UpdateInfo(
        project=project,
        language="python",
        package=package,
        current=current,
        latest=latest,
    )


def _make_digest(*updates: UpdateInfo) -> ProjectDigest:
    return ProjectDigest(updates=list(updates))


# ---------------------------------------------------------------------------
# ImpactEntry
# ---------------------------------------------------------------------------

def test_impact_entry_to_dict_keys():
    entry = ImpactEntry(package="requests", latest="2.32.0", bump="minor", affected_projects=["a"])
    d = entry.to_dict()
    assert set(d) == {"package", "latest", "bump", "affected_projects", "project_count"}


def test_impact_entry_project_count():
    entry = ImpactEntry(package="flask", latest="3.0.0", bump="major", affected_projects=["a", "b"])
    assert entry.to_dict()["project_count"] == 2


def test_impact_entry_str_contains_package():
    entry = ImpactEntry(package="flask", latest="3.0.0", bump="major", affected_projects=["svc"])
    assert "flask" in str(entry)
    assert "3.0.0" in str(entry)
    assert "major" in str(entry)


# ---------------------------------------------------------------------------
# ImpactReport
# ---------------------------------------------------------------------------

def test_impact_report_is_empty_when_no_entries():
    report = ImpactReport()
    assert report.is_empty()


def test_impact_report_not_empty_with_entries():
    entry = ImpactEntry(package="x", latest="1.0.0", bump="major", affected_projects=["p"])
    report = ImpactReport(entries=[entry])
    assert not report.is_empty()


def test_impact_report_to_dict_structure():
    entry = ImpactEntry(package="x", latest="1.0.0", bump="major", affected_projects=["p"])
    report = ImpactReport(entries=[entry])
    d = report.to_dict()
    assert d["total_packages"] == 1
    assert len(d["entries"]) == 1


def test_impact_report_high_impact_filters_by_count():
    e1 = ImpactEntry(package="a", latest="1.0", bump="major", affected_projects=["p1", "p2"])
    e2 = ImpactEntry(package="b", latest="1.0", bump="minor", affected_projects=["p1"])
    report = ImpactReport(entries=[e1, e2])
    hi = report.high_impact(min_projects=2)
    assert len(hi) == 1
    assert hi[0].package == "a"


# ---------------------------------------------------------------------------
# build_impact_report
# ---------------------------------------------------------------------------

def test_build_impact_report_empty_digests():
    report = build_impact_report({})
    assert report.is_empty()


def test_build_impact_report_single_project():
    u = _make_update("requests", "2.28.0", "2.32.0", project="api")
    digests = {"api": _make_digest(u)}
    report = build_impact_report(digests)
    assert len(report.entries) == 1
    assert report.entries[0].package == "requests"
    assert report.entries[0].affected_projects == ["api"]


def test_build_impact_report_shared_package_across_projects():
    u1 = _make_update("flask", "2.3.0", "3.0.0", project="web")
    u2 = _make_update("flask", "2.3.0", "3.0.0", project="admin")
    digests = {"web": _make_digest(u1), "admin": _make_digest(u2)}
    report = build_impact_report(digests)
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert set(entry.affected_projects) == {"web", "admin"}
    assert entry.to_dict()["project_count"] == 2


def test_build_impact_report_sorted_by_project_count_desc():
    u_shared1 = _make_update("shared", "1.0", "2.0", project="p1")
    u_shared2 = _make_update("shared", "1.0", "2.0", project="p2")
    u_single = _make_update("solo", "0.1", "0.2", project="p1")
    digests = {
        "p1": _make_digest(u_shared1, u_single),
        "p2": _make_digest(u_shared2),
    }
    report = build_impact_report(digests)
    assert report.entries[0].package == "shared"


def test_build_impact_report_bump_level_captured():
    u = _make_update("django", "4.2.0", "5.0.0", project="site")
    report = build_impact_report({"site": _make_digest(u)})
    assert report.entries[0].bump == "major"
