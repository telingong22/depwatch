"""Tests for depwatch.scoring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from depwatch.scoring import (
    PriorityScore,
    _stale_days,
    rank_updates,
    score_update,
)


def _make_update(
    package: str = "requests",
    project: str = "my-app",
    current: str = "1.0.0",
    latest: str = "2.0.0",
    published_at: str | None = None,
):
    release_info = SimpleNamespace(published_at=published_at)
    return SimpleNamespace(
        package_name=package,
        project_name=project,
        current_version=current,
        latest_version=latest,
        release_info=release_info,
    )


# ---------------------------------------------------------------------------
# _stale_days
# ---------------------------------------------------------------------------

def test_stale_days_none_returns_zero():
    assert _stale_days(None) == 0


def test_stale_days_invalid_string_returns_zero():
    assert _stale_days("not-a-date") == 0


def test_stale_days_recent_is_zero_or_one():
    now = datetime.now(timezone.utc).isoformat()
    assert _stale_days(now) in (0, 1)


def test_stale_days_capped_at_30():
    old = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    assert _stale_days(old) == 30


def test_stale_days_exact_10():
    ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    assert _stale_days(ts) == 10


# ---------------------------------------------------------------------------
# score_update
# ---------------------------------------------------------------------------

def test_score_major_bump_base():
    u = _make_update(current="1.0.0", latest="2.0.0")
    ps = score_update(u)
    assert ps.breakdown["bump"] == 40
    assert ps.breakdown["security"] == 0


def test_score_minor_bump_base():
    u = _make_update(current="1.0.0", latest="1.1.0")
    ps = score_update(u)
    assert ps.breakdown["bump"] == 20


def test_score_patch_bump_base():
    u = _make_update(current="1.0.0", latest="1.0.1")
    ps = score_update(u)
    assert ps.breakdown["bump"] == 5


def test_score_security_bonus_added():
    u = _make_update(package="cryptography", current="1.0", latest="2.0")
    ps = score_update(u, security_packages=["cryptography"])
    assert ps.breakdown["security"] == 50
    assert ps.score == 40 + 50  # major + security (no stale)


def test_score_security_case_insensitive():
    u = _make_update(package="Cryptography", current="1.0", latest="2.0")
    ps = score_update(u, security_packages=["cryptography"])
    assert ps.breakdown["security"] == 50


def test_score_to_dict_has_expected_keys():
    u = _make_update()
    ps = score_update(u)
    d = ps.to_dict()
    assert set(d.keys()) == {"package", "project", "score", "breakdown"}


# ---------------------------------------------------------------------------
# rank_updates
# ---------------------------------------------------------------------------

def test_rank_updates_sorted_descending():
    u_patch = _make_update(package="a", current="1.0.0", latest="1.0.1")
    u_major = _make_update(package="b", current="1.0.0", latest="2.0.0")
    u_minor = _make_update(package="c", current="1.0.0", latest="1.1.0")
    ranked = rank_updates([u_patch, u_major, u_minor])
    scores = [ps.score for _, ps in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_updates_empty_list():
    assert rank_updates([]) == []


def test_rank_updates_returns_all_items():
    updates = [_make_update(package=f"pkg{i}") for i in range(5)]
    ranked = rank_updates(updates)
    assert len(ranked) == 5
