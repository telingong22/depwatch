"""Unit tests for depwatch.recommendations."""
from __future__ import annotations

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.recommendations import (
    Recommendation,
    RecommendationReport,
    _priority_for_update,
    build_recommendations,
)


def _make_update(package: str, current: str, latest: str, lang: str = "python") -> UpdateInfo:
    return UpdateInfo(
        package_name=package,
        current_version=current,
        latest_version=latest,
        language=lang,
    )


def _make_digest(name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=name, updates=updates)


# --- Recommendation dataclass ---

def test_recommendation_to_dict_keys():
    r = Recommendation("proj", "pkg", "1.0", "2.0", "major version bump", "high")
    d = r.to_dict()
    assert set(d.keys()) == {"project", "package", "current_version", "latest_version", "reason", "priority"}


def test_recommendation_str_contains_priority():
    r = Recommendation("proj", "pkg", "1.0", "2.0", "major version bump", "high")
    assert "HIGH" in str(r)
    assert "pkg" in str(r)


# --- RecommendationReport ---

def test_report_is_empty_when_no_items():
    report = RecommendationReport()
    assert report.is_empty()


def test_report_not_empty_with_items():
    r = Recommendation("p", "q", "1", "2", "reason", "low")
    report = RecommendationReport(items=[r])
    assert not report.is_empty()


def test_report_by_priority_filters():
    high = Recommendation("p", "a", "1", "2", "r", "high")
    low = Recommendation("p", "b", "1", "2", "r", "low")
    report = RecommendationReport(items=[high, low])
    assert report.by_priority("high") == [high]
    assert report.by_priority("low") == [low]
    assert report.by_priority("medium") == []


def test_report_to_dict_structure():
    high = Recommendation("p", "a", "1", "2", "r", "high")
    report = RecommendationReport(items=[high])
    d = report.to_dict()
    assert d["total"] == 1
    assert d["high"] == 1
    assert d["medium"] == 0
    assert d["low"] == 0
    assert len(d["items"]) == 1


# --- _priority_for_update ---

def test_priority_major_bump_is_high():
    u = _make_update("pkg", "1.2.3", "2.0.0")
    priority, reason = _priority_for_update(u)
    assert priority == "high"
    assert "major" in reason


def test_priority_unknown_current_is_medium():
    u = _make_update("pkg", "unknown", "1.2.3")
    priority, _ = _priority_for_update(u)
    assert priority == "medium"


def test_priority_minor_is_low():
    u = _make_update("pkg", "1.2.3", "1.3.0")
    priority, _ = _priority_for_update(u)
    assert priority == "low"


# --- build_recommendations ---

def test_build_recommendations_empty_digests():
    report = build_recommendations([])
    assert report.is_empty()


def test_build_recommendations_sorted_high_first():
    d = _make_digest("proj", [
        _make_update("a", "1.0", "1.1"),   # low
        _make_update("b", "1.0", "2.0"),   # high
    ])
    report = build_recommendations([d])
    assert report.items[0].priority == "high"
    assert report.items[1].priority == "low"


def test_build_recommendations_project_name_preserved():
    d = _make_digest("myproject", [_make_update("pkg", "1.0", "2.0")])
    report = build_recommendations([d])
    assert report.items[0].project == "myproject"


def test_build_recommendations_multiple_digests():
    d1 = _make_digest("p1", [_make_update("a", "1.0", "2.0")])
    d2 = _make_digest("p2", [_make_update("b", "1.0", "1.1")])
    report = build_recommendations([d1, d2])
    assert len(report.items) == 2
