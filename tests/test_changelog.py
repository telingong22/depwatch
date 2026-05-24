"""Tests for depwatch.changelog."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional
from unittest.mock import patch, MagicMock
import urllib.error

import pytest

from depwatch.changelog import (
    ChangelogInfo,
    _pypi_changelog_url,
    _go_changelog_url,
    fetch_changelog,
    fetch_changelogs_for_updates,
)


# ---------------------------------------------------------------------------
# Minimal stub that mimics UpdateInfo enough for fetch_changelogs_for_updates
# ---------------------------------------------------------------------------
@dataclass
class _FakeUpdate:
    package: str
    language: str
    latest: str
    current: str = "1.0.0"


# ---------------------------------------------------------------------------
# ChangelogInfo.to_dict
# ---------------------------------------------------------------------------

def test_changelog_info_to_dict_keys():
    info = ChangelogInfo(package="requests", language="python", version="2.31.0",
                         url="https://example.com", summary=None)
    d = info.to_dict()
    assert set(d.keys()) == {"package", "language", "version", "url", "summary"}


def test_changelog_info_to_dict_values():
    info = ChangelogInfo(package="requests", language="python", version="2.31.0",
                         url="https://example.com", summary="fixes")
    d = info.to_dict()
    assert d["package"] == "requests"
    assert d["url"] == "https://example.com"
    assert d["summary"] == "fixes"


# ---------------------------------------------------------------------------
# _pypi_changelog_url
# ---------------------------------------------------------------------------

def _make_pypi_response(project_urls: dict, home_page: str = "") -> MagicMock:
    payload = {"info": {"project_urls": project_urls, "home_page": home_page}}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_pypi_changelog_url_found():
    mock_resp = _make_pypi_response({"Changelog": "https://changelog.example.com"})
    with patch("urllib.request.urlopen", return_value=mock_resp):
        url = _pypi_changelog_url("requests", "2.31.0")
    assert url == "https://changelog.example.com"


def test_pypi_changelog_url_falls_back_to_homepage():
    mock_resp = _make_pypi_response({}, home_page="https://home.example.com")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        url = _pypi_changelog_url("requests", "2.31.0")
    assert url == "https://home.example.com"


def test_pypi_changelog_url_network_error():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("err")):
        url = _pypi_changelog_url("requests", "2.31.0")
    assert url is None


def test_pypi_changelog_url_bad_json():
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"not-json"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        url = _pypi_changelog_url("requests", "2.31.0")
    assert url is None


# ---------------------------------------------------------------------------
# _go_changelog_url
# ---------------------------------------------------------------------------

def test_go_changelog_url_github_module():
    url = _go_changelog_url("github.com/gin-gonic/gin", "v1.9.0")
    assert url == "https://github.com/gin-gonic/gin/releases/tag/v1.9.0"


def test_go_changelog_url_adds_v_prefix():
    url = _go_changelog_url("github.com/gin-gonic/gin", "1.9.0")
    assert url == "https://github.com/gin-gonic/gin/releases/tag/v1.9.0"


def test_go_changelog_url_non_github_returns_none():
    url = _go_changelog_url("golang.org/x/text", "v0.14.0")
    assert url is None


# ---------------------------------------------------------------------------
# fetch_changelog
# ---------------------------------------------------------------------------

def test_fetch_changelog_python_returns_changelog_info():
    with patch("depwatch.changelog._pypi_changelog_url", return_value="https://example.com"):
        info = fetch_changelog("requests", "python", "2.31.0")
    assert isinstance(info, ChangelogInfo)
    assert info.url == "https://example.com"
    assert info.language == "python"


def test_fetch_changelog_go_returns_changelog_info():
    info = fetch_changelog("github.com/gin-gonic/gin", "go", "v1.9.0")
    assert isinstance(info, ChangelogInfo)
    assert "gin" in (info.url or "")


def test_fetch_changelog_unknown_language_url_is_none():
    info = fetch_changelog("somepkg", "rust", "1.0.0")
    assert info.url is None


# ---------------------------------------------------------------------------
# fetch_changelogs_for_updates
# ---------------------------------------------------------------------------

def test_fetch_changelogs_for_updates_length():
    updates = [
        _FakeUpdate(package="requests", language="python", latest="2.31.0"),
        _FakeUpdate(package="flask", language="python", latest="3.0.0"),
    ]
    with patch("depwatch.changelog._pypi_changelog_url", return_value=None):
        results = fetch_changelogs_for_updates(updates)
    assert len(results) == 2


def test_fetch_changelogs_for_updates_empty():
    assert fetch_changelogs_for_updates([]) == []
