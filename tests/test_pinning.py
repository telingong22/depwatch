"""Unit tests for depwatch.pinning."""
from __future__ import annotations

import pytest

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.pinning import (
    PinSuggestion,
    _format_pin,
    build_pin_suggestions,
    suggestions_to_text,
)


def _make_update(package: str, current: str, latest: str, language: str = "python") -> UpdateInfo:
    return UpdateInfo(
        project="myproject",
        package=package,
        language=language,
        current_version=current,
        latest_version=latest,
    )


def _make_digest(name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=name, updates=updates)


# --- _format_pin ---

def test_format_pin_python():
    assert _format_pin("python", "requests", "2.31.0") == "requests==2.31.0"


def test_format_pin_go_strips_v():
    assert _format_pin("go", "github.com/gin-gonic/gin", "v1.9.1") == "github.com/gin-gonic/gin v1.9.1"


def test_format_pin_go_adds_v_prefix():
    assert _format_pin("go", "github.com/foo/bar", "1.2.3") == "github.com/foo/bar v1.2.3"


def test_format_pin_unknown_language():
    assert _format_pin("ruby", "rails", "7.0.0") == "rails@7.0.0"


# --- build_pin_suggestions ---

def test_build_pin_suggestions_empty_digests():
    assert build_pin_suggestions([]) == []


def test_build_pin_suggestions_no_updates():
    digest = _make_digest("proj", [])
    assert build_pin_suggestions([digest]) == []


def test_build_pin_suggestions_single_update():
    u = _make_update("requests", "2.28.0", "2.31.0")
    digest = _make_digest("proj", [u])
    result = build_pin_suggestions([digest])
    assert len(result) == 1
    assert result[0].suggested_pin == "requests==2.31.0"
    assert result[0].current == "2.28.0"
    assert result[0].project == "proj"


def test_build_pin_suggestions_multiple_projects():
    d1 = _make_digest("proj1", [_make_update("flask", "2.0", "3.0")])
    d2 = _make_digest("proj2", [_make_update("numpy", "1.23", "1.26")])
    result = build_pin_suggestions([d1, d2])
    assert len(result) == 2
    projects = {s.project for s in result}
    assert projects == {"proj1", "proj2"}


def test_build_pin_suggestions_go_package():
    u = _make_update("github.com/pkg/errors", "0.9.0", "0.9.1", language="go")
    digest = _make_digest("goproject", [u])
    result = build_pin_suggestions([digest])
    assert result[0].suggested_pin == "github.com/pkg/errors v0.9.1"


# --- PinSuggestion ---

def test_pin_suggestion_str():
    s = PinSuggestion(
        project="p", package="requests", language="python",
        current="2.28.0", suggested_pin="requests==2.31.0",
    )
    assert "requests==2.31.0" in str(s)
    assert "2.28.0" in str(s)


def test_pin_suggestion_to_dict_keys():
    s = PinSuggestion(
        project="p", package="requests", language="python",
        current="2.28.0", suggested_pin="requests==2.31.0",
    )
    d = s.to_dict()
    assert set(d.keys()) == {"project", "package", "language", "current", "suggested_pin"}


# --- suggestions_to_text ---

def test_suggestions_to_text_empty():
    text = suggestions_to_text([])
    assert "up to date" in text


def test_suggestions_to_text_non_empty():
    s = PinSuggestion(
        project="p", package="requests", language="python",
        current="2.28.0", suggested_pin="requests==2.31.0",
    )
    text = suggestions_to_text([s])
    assert "Pin suggestions" in text
    assert "requests==2.31.0" in text
