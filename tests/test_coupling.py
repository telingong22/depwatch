"""Unit tests for depwatch.coupling."""
from __future__ import annotations

from depwatch.coupling import (
    CoupledPackage,
    CouplingReport,
    build_coupling_report,
)
from depwatch.digest import ProjectDigest
from depwatch.checker import UpdateInfo


def _make_update(package: str, language: str = "python", latest: str = "2.0.0") -> UpdateInfo:
    return UpdateInfo(
        package=package,
        current_version="1.0.0",
        latest_version=latest,
        language=language,
    )


def _make_digest(project: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=project, updates=updates)


def test_coupled_package_to_dict_keys():
    cp = CoupledPackage("requests", "python", ["a", "b"], "2.28.0")
    d = cp.to_dict()
    assert set(d.keys()) == {"package", "language", "projects", "latest_version", "project_count"}


def test_coupled_package_project_count():
    cp = CoupledPackage("requests", "python", ["a", "b", "c"], "2.28.0")
    assert cp.to_dict()["project_count"] == 3


def test_coupled_package_str():
    cp = CoupledPackage("requests", "python", ["proj-b", "proj-a"], "2.28.0")
    s = str(cp)
    assert "requests" in s
    assert "proj-a" in s
    assert "proj-b" in s


def test_coupling_report_is_empty_when_no_coupled():
    report = CouplingReport(coupled=[])
    assert report.is_empty()


def test_coupling_report_not_empty_with_entries():
    cp = CoupledPackage("requests", "python", ["a", "b"], "2.0.0")
    report = CouplingReport(coupled=[cp])
    assert not report.is_empty()


def test_coupling_report_to_dict_structure():
    cp = CoupledPackage("requests", "python", ["a", "b"], "2.0.0")
    report = CouplingReport(coupled=[cp])
    d = report.to_dict()
    assert d["total"] == 1
    assert len(d["coupled_packages"]) == 1


def test_coupling_report_summary_empty():
    report = CouplingReport()
    assert "No coupled" in report.summary()


def test_coupling_report_summary_non_empty():
    cp = CoupledPackage("requests", "python", ["a", "b"], "2.0.0")
    report = CouplingReport(coupled=[cp])
    summary = report.summary()
    assert "requests" in summary
    assert "Coupled packages" in summary


def test_build_coupling_report_no_shared():
    d1 = _make_digest("proj-a", [_make_update("requests")])
    d2 = _make_digest("proj-b", [_make_update("flask")])
    report = build_coupling_report([d1, d2])
    assert report.is_empty()


def test_build_coupling_report_one_shared():
    d1 = _make_digest("proj-a", [_make_update("requests")])
    d2 = _make_digest("proj-b", [_make_update("requests")])
    report = build_coupling_report([d1, d2])
    assert not report.is_empty()
    assert len(report.coupled) == 1
    assert report.coupled[0].package == "requests"
    assert set(report.coupled[0].projects) == {"proj-a", "proj-b"}


def test_build_coupling_report_multiple_shared():
    d1 = _make_digest("proj-a", [_make_update("requests"), _make_update("flask")])
    d2 = _make_digest("proj-b", [_make_update("requests"), _make_update("flask")])
    report = build_coupling_report([d1, d2])
    packages = {c.package for c in report.coupled}
    assert packages == {"requests", "flask"}


def test_build_coupling_report_three_projects():
    d1 = _make_digest("a", [_make_update("requests")])
    d2 = _make_digest("b", [_make_update("requests")])
    d3 = _make_digest("c", [_make_update("requests")])
    report = build_coupling_report([d1, d2, d3])
    assert report.coupled[0].to_dict()["project_count"] == 3


def test_build_coupling_report_language_distinguishes_packages():
    d1 = _make_digest("proj-a", [_make_update("http", language="python")])
    d2 = _make_digest("proj-b", [_make_update("http", language="go")])
    report = build_coupling_report([d1, d2])
    # Different languages — not coupled
    assert report.is_empty()


def test_build_coupling_sorted_by_project_count_desc():
    d1 = _make_digest("a", [_make_update("alpha"), _make_update("beta")])
    d2 = _make_digest("b", [_make_update("alpha"), _make_update("beta")])
    d3 = _make_digest("c", [_make_update("alpha")])
    report = build_coupling_report([d1, d2, d3])
    # alpha shared by 3, beta by 2
    assert report.coupled[0].package == "alpha"
    assert report.coupled[1].package == "beta"
