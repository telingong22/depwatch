"""Integration tests for the recommendations pipeline."""
from __future__ import annotations

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.recommendations import build_recommendations


def _u(pkg: str, current: str, latest: str, lang: str = "python") -> UpdateInfo:
    return UpdateInfo(
        package_name=pkg,
        current_version=current,
        latest_version=latest,
        language=lang,
    )


def _d(name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=name, updates=updates)


def test_all_high_priority_come_first():
    d = _d("proj", [
        _u("patch-pkg", "1.0.0", "1.0.1"),
        _u("major-pkg", "1.0.0", "3.0.0"),
        _u("minor-pkg", "1.0.0", "1.5.0"),
    ])
    report = build_recommendations([d])
    priorities = [r.priority for r in report.items]
    assert priorities[0] == "high"


def test_unpinned_package_gets_medium_priority():
    d = _d("proj", [_u("lib", "unknown", "1.2.3")])
    report = build_recommendations([d])
    assert report.items[0].priority == "medium"


def test_go_packages_handled_same_as_python():
    d = _d("goproject", [_u("github.com/foo/bar", "v1.0.0", "v2.0.0", "go")])
    report = build_recommendations([d])
    assert report.items[0].priority == "high"
    assert report.items[0].project == "goproject"


def test_empty_updates_produce_empty_report():
    d = _d("empty", [])
    report = build_recommendations([d])
    assert report.is_empty()


def test_to_dict_round_trip_preserves_counts():
    d = _d("proj", [
        _u("a", "1.0", "2.0"),
        _u("b", "1.0", "1.1"),
    ])
    report = build_recommendations([d])
    d_out = report.to_dict()
    assert d_out["total"] == 2
    assert d_out["high"] + d_out["medium"] + d_out["low"] == 2
