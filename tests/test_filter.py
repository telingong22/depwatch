"""Tests for depwatch.filter."""
from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.filter import FilterConfig, _bump_level, _is_ignored, apply_filter


def _make_update(package: str, current: str, latest: str) -> UpdateInfo:
    return UpdateInfo(package=package, current_version=current, latest_version=latest)


# ---------------------------------------------------------------------------
# _bump_level
# ---------------------------------------------------------------------------

def test_bump_level_major():
    assert _bump_level("1.2.3", "2.0.0") == "major"


def test_bump_level_minor():
    assert _bump_level("1.2.3", "1.3.0") == "minor"


def test_bump_level_patch():
    assert _bump_level("1.2.3", "1.2.4") == "patch"


def test_bump_level_v_prefix():
    assert _bump_level("v1.0.0", "v2.0.0") == "major"


def test_bump_level_non_numeric_treated_as_zero():
    # non-numeric segment → treated as 0; 0.0.alpha vs 0.0.beta both → patch
    assert _bump_level("0.0.alpha", "0.0.beta") == "patch"


# ---------------------------------------------------------------------------
# _is_ignored
# ---------------------------------------------------------------------------

def test_is_ignored_exact_match():
    assert _is_ignored("boto3", ["boto3"]) is True


def test_is_ignored_glob_match():
    assert _is_ignored("internal-utils", ["internal-*"]) is True


def test_is_ignored_no_match():
    assert _is_ignored("requests", ["boto3", "internal-*"]) is False


# ---------------------------------------------------------------------------
# apply_filter
# ---------------------------------------------------------------------------

def test_apply_filter_removes_ignored_package():
    updates = [_make_update("boto3", "1.0.0", "2.0.0")]
    cfg = FilterConfig(ignore_packages=["boto3"])
    assert apply_filter(updates, cfg) == []


def test_apply_filter_keeps_non_ignored():
    updates = [_make_update("requests", "2.27.0", "2.28.0")]
    cfg = FilterConfig(ignore_packages=["boto3"])
    assert len(apply_filter(updates, cfg)) == 1


def test_apply_filter_min_bump_major_drops_minor():
    updates = [_make_update("requests", "2.27.0", "2.28.0")]
    cfg = FilterConfig(min_bump="major")
    assert apply_filter(updates, cfg) == []


def test_apply_filter_min_bump_major_keeps_major():
    updates = [_make_update("requests", "2.27.0", "3.0.0")]
    cfg = FilterConfig(min_bump="major")
    assert len(apply_filter(updates, cfg)) == 1


def test_apply_filter_min_bump_minor_keeps_minor():
    updates = [_make_update("django", "4.1.0", "4.2.0")]
    cfg = FilterConfig(min_bump="minor")
    assert len(apply_filter(updates, cfg)) == 1


def test_apply_filter_min_bump_minor_drops_patch():
    updates = [_make_update("django", "4.1.0", "4.1.1")]
    cfg = FilterConfig(min_bump="minor")
    assert apply_filter(updates, cfg) == []


def test_apply_filter_empty_input():
    assert apply_filter([], FilterConfig()) == []


def test_apply_filter_glob_ignore():
    updates = [
        _make_update("internal-auth", "1.0.0", "2.0.0"),
        _make_update("requests", "2.27.0", "3.0.0"),
    ]
    cfg = FilterConfig(ignore_packages=["internal-*"])
    result = apply_filter(updates, cfg)
    assert len(result) == 1
    assert result[0].package == "requests"
