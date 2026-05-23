"""Tests for depwatch.dedup."""

from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.dedup import DeduplicatedResult, _update_key, dedup_updates


def _make_update(
    package: str = "requests",
    current: str = "2.28.0",
    latest: str = "2.29.0",
    project: str = "my-project",
) -> UpdateInfo:
    return UpdateInfo(
        project_name=project,
        package_name=package,
        current_version=current,
        latest_version=latest,
    )


# ---------------------------------------------------------------------------
# _update_key
# ---------------------------------------------------------------------------

def test_update_key_includes_project_and_package_and_latest():
    u = _make_update(package="flask", latest="3.0.0", project="proj")
    key = _update_key(u)
    assert "flask" in key
    assert "3.0.0" in key
    assert "proj" in key


def test_update_key_ignores_current_version():
    u1 = _make_update(current="1.0.0", latest="2.0.0")
    u2 = _make_update(current="1.5.0", latest="2.0.0")
    assert _update_key(u1) == _update_key(u2)


# ---------------------------------------------------------------------------
# DeduplicatedResult
# ---------------------------------------------------------------------------

def test_deduplicated_result_is_empty_when_no_updates():
    result = DeduplicatedResult()
    assert result.is_empty()


def test_deduplicated_result_not_empty_with_updates():
    result = DeduplicatedResult(updates=[_make_update()])
    assert not result.is_empty()


def test_deduplicated_result_dropped_count():
    result = DeduplicatedResult(dropped=[_make_update(), _make_update()])
    assert result.dropped_count() == 2


# ---------------------------------------------------------------------------
# dedup_updates
# ---------------------------------------------------------------------------

def test_dedup_empty_input():
    result = dedup_updates([])
    assert result.is_empty()
    assert result.dropped_count() == 0


def test_dedup_no_duplicates_returns_all():
    updates = [
        _make_update(package="requests", latest="2.29.0"),
        _make_update(package="flask", latest="3.0.0"),
    ]
    result = dedup_updates(updates)
    assert len(result.updates) == 2
    assert result.dropped_count() == 0


def test_dedup_removes_exact_duplicate():
    u = _make_update()
    result = dedup_updates([u, u])
    assert len(result.updates) == 1
    assert result.dropped_count() == 1


def test_dedup_keeps_first_occurrence():
    u1 = _make_update(current="1.0.0", latest="2.0.0")
    u2 = _make_update(current="1.5.0", latest="2.0.0")  # same key, different current
    result = dedup_updates([u1, u2])
    assert result.updates[0].current_version == "1.0.0"
    assert result.dropped_count() == 1


def test_dedup_different_projects_not_deduped():
    u1 = _make_update(package="requests", project="proj-a")
    u2 = _make_update(package="requests", project="proj-b")
    result = dedup_updates([u1, u2])
    assert len(result.updates) == 2


def test_dedup_different_latest_versions_not_deduped():
    u1 = _make_update(latest="2.0.0")
    u2 = _make_update(latest="2.1.0")
    result = dedup_updates([u1, u2])
    assert len(result.updates) == 2


def test_dedup_preserves_order_of_unique_updates():
    updates = [
        _make_update(package="alpha", latest="1.0.0"),
        _make_update(package="beta", latest="1.0.0"),
        _make_update(package="gamma", latest="1.0.0"),
    ]
    result = dedup_updates(updates)
    names = [u.package_name for u in result.updates]
    assert names == ["alpha", "beta", "gamma"]
