"""Tests for depwatch.checker module."""

from unittest.mock import patch, MagicMock

import pytest

from depwatch.checker import UpdateInfo, _is_newer, check_package, check_project
from depwatch.config import ProjectConfig
from depwatch.fetcher import ReleaseInfo


# ---------------------------------------------------------------------------
# _is_newer
# ---------------------------------------------------------------------------

def test_is_newer_true():
    assert _is_newer("1.0.0", "2.0.0") is True


def test_is_newer_false_same():
    assert _is_newer("1.0.0", "1.0.0") is False


def test_is_newer_false_older():
    assert _is_newer("2.0.0", "1.9.9") is False


def test_is_newer_invalid_version_fallback():
    # Falls back to string comparison when versions are unparseable
    assert _is_newer("abc", "xyz") is True
    assert _is_newer("abc", "abc") is False


# ---------------------------------------------------------------------------
# check_package
# ---------------------------------------------------------------------------

def _make_release(version: str, url: str = "https://example.com") -> ReleaseInfo:
    return ReleaseInfo(version=version, url=url)


def test_check_package_outdated():
    with patch("depwatch.checker.fetch_latest", return_value=_make_release("2.0.0")):
        result = check_package("requests", "1.0.0", "python")
    assert result is not None
    assert result.is_outdated is True
    assert result.latest_version == "2.0.0"
    assert result.current_version == "1.0.0"


def test_check_package_up_to_date():
    with patch("depwatch.checker.fetch_latest", return_value=_make_release("1.0.0")):
        result = check_package("requests", "1.0.0", "python")
    assert result is not None
    assert result.is_outdated is False


def test_check_package_fetch_returns_none():
    with patch("depwatch.checker.fetch_latest", return_value=None):
        result = check_package("unknown-pkg", "1.0.0", "python")
    assert result is None


# ---------------------------------------------------------------------------
# check_project
# ---------------------------------------------------------------------------

def _make_project(deps: dict) -> ProjectConfig:
    return ProjectConfig(
        name="test-project",
        language="python",
        path="/tmp/fake",
        dependencies=deps,
    )


def test_check_project_returns_all_resolvable():
    releases = {
        "requests": _make_release("2.0.0"),
        "flask": _make_release("3.0.0"),
    }

    def fake_fetch(package, language):
        return releases.get(package)

    project = _make_project({"requests": "1.0.0", "flask": "3.0.0", "missing": "0.1"})
    with patch("depwatch.checker.fetch_latest", side_effect=fake_fetch):
        results = check_project(project)

    assert len(results) == 2  # 'missing' is excluded
    names = {r.package for r in results}
    assert names == {"requests", "flask"}


def test_check_project_empty_dependencies():
    project = _make_project({})
    with patch("depwatch.checker.fetch_latest") as mock_fetch:
        results = check_project(project)
    mock_fetch.assert_not_called()
    assert results == []
