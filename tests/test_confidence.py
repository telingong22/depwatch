"""Tests for depwatch.confidence."""
from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.confidence import (
    ConfidenceScore,
    ConfidenceReport,
    _score_update,
    build_confidence_report,
)


def _make_update(
    package: str = "requests",
    current: str = "2.28.0",
    latest: str = "2.29.0",
    language: str = "python",
    project: str = "myapp",
) -> UpdateInfo:
    return UpdateInfo(
        project=project,
        package=package,
        language=language,
        current_version=current,
        latest_version=latest,
    )


def _make_digest(updates=None, project="myapp") -> ProjectDigest:
    return ProjectDigest(project=project, updates=updates or [])


# --- ConfidenceScore ---

def test_confidence_score_to_dict_keys():
    cs = ConfidenceScore(
        project="p", package="pkg", language="python",
        current_version="1.0", latest_version="2.0",
        score=0.75, reasons=["pinned"],
    )
    d = cs.to_dict()
    assert set(d.keys()) == {"project", "package", "language", "current_version", "latest_version", "score", "reasons"}


def test_confidence_score_str_contains_package():
    cs = ConfidenceScore(
        project="p", package="flask", language="python",
        current_version="2.0", latest_version="3.0",
        score=0.8, reasons=["stable"],
    )
    assert "flask" in str(cs)
    assert "80%" in str(cs)


# --- _score_update ---

def test_pinned_version_boosts_score():
    u = _make_update(current="1.0.0", latest="2.0.0")
    cs = _score_update(u)
    assert any("pinned" in r for r in cs.reasons)
    assert cs.score > 0.5


def test_unpinned_version_lowers_score():
    u = _make_update(current="unknown", latest="2.0.0")
    cs = _score_update(u)
    assert any("unpinned" in r for r in cs.reasons)


def test_pre_release_lowers_score():
    u = _make_update(current="1.0.0", latest="2.0.0rc1")
    cs = _score_update(u)
    assert any("pre-release" in r for r in cs.reasons)


def test_stable_release_boosts_score():
    u = _make_update(current="1.0.0", latest="2.0.0")
    cs = _score_update(u)
    assert any("stable" in r for r in cs.reasons)


def test_go_language_adds_small_boost():
    u = _make_update(current="v1.2.0", latest="v1.3.0", language="go")
    cs = _score_update(u)
    assert any("Go module" in r for r in cs.reasons)


def test_score_clamped_between_zero_and_one():
    u = _make_update(current="unknown", latest="2.0.0alpha")
    cs = _score_update(u)
    assert 0.0 <= cs.score <= 1.0


# --- build_confidence_report ---

def test_report_is_empty_for_no_digests():
    report = build_confidence_report([])
    assert report.is_empty()


def test_report_has_entry_per_update():
    digest = _make_digest(updates=[
        _make_update(package="a"),
        _make_update(package="b"),
    ])
    report = build_confidence_report([digest])
    assert len(report.entries) == 2


def test_report_sorted_by_score_descending():
    digest = _make_digest(updates=[
        _make_update(package="low", current="unknown", latest="1.0.0alpha"),
        _make_update(package="high", current="1.0.0", latest="2.0.0"),
    ])
    report = build_confidence_report([digest])
    assert report.entries[0].score >= report.entries[1].score


def test_report_to_dict_has_entries_key():
    digest = _make_digest(updates=[_make_update()])
    report = build_confidence_report([digest])
    d = report.to_dict()
    assert "entries" in d
    assert isinstance(d["entries"], list)
