"""Tests for depwatch.summarizer."""
import pytest

from depwatch.summarizer import (
    SummaryLine,
    Summary,
    build_summary,
    _lines_from_digest,
)
from depwatch.notifier import DigestPayload
from depwatch.digest import ProjectDigest
from depwatch.checker import UpdateInfo


def _make_update(package: str, current: str, latest: str) -> UpdateInfo:
    return UpdateInfo(package=package, current_version=current, latest_version=latest)


def _make_digest(name: str, language: str, updates) -> ProjectDigest:
    return ProjectDigest(project_name=name, language=language, updates=updates)


# --- SummaryLine ---

def test_summary_line_str():
    line = SummaryLine(
        project="myapp", package="requests", current="2.28.0",
        latest="2.31.0", language="python"
    )
    text = str(line)
    assert "myapp" in text
    assert "requests" in text
    assert "2.28.0" in text
    assert "2.31.0" in text
    assert "python" in text


# --- Summary ---

def test_summary_is_empty_true():
    s = Summary(lines=[])
    assert s.is_empty()


def test_summary_is_empty_false():
    line = SummaryLine("p", "pkg", "1.0", "2.0", "go")
    s = Summary(lines=[line])
    assert not s.is_empty()


def test_summary_to_text_empty():
    s = Summary(lines=[])
    assert s.to_text() == "No updates found."


def test_summary_to_text_with_updates():
    line = SummaryLine("proj", "flask", "2.0.0", "3.0.0", "python")
    s = Summary(lines=[line])
    text = s.to_text()
    assert "1 update(s)" in text
    assert "flask" in text
    assert "2.0.0" in text
    assert "3.0.0" in text


def test_summary_to_dict_structure():
    line = SummaryLine("proj", "gin", "1.8.0", "1.9.0", "go")
    s = Summary(lines=[line])
    d = s.to_dict()
    assert d["total"] == 1
    entry = d["updates"][0]
    assert entry["project"] == "proj"
    assert entry["package"] == "gin"
    assert entry["current"] == "1.8.0"
    assert entry["latest"] == "1.9.0"
    assert entry["language"] == "go"


# --- _lines_from_digest ---

def test_lines_from_digest_empty():
    digest = _make_digest("proj", "python", [])
    assert _lines_from_digest(digest) == []


def test_lines_from_digest_unknown_current():
    update = UpdateInfo(package="boto3", current_version=None, latest_version="1.34.0")
    digest = _make_digest("proj", "python", [update])
    lines = _lines_from_digest(digest)
    assert len(lines) == 1
    assert lines[0].current == "unknown"


# --- build_summary ---

def test_build_summary_empty_payload():
    payload = DigestPayload(digests=[])
    summary = build_summary(payload)
    assert summary.is_empty()


def test_build_summary_aggregates_all_projects():
    d1 = _make_digest("app1", "python", [_make_update("requests", "2.0", "3.0")])
    d2 = _make_digest("app2", "go", [_make_update("gin", "1.0", "2.0"), _make_update("zap", "1.0", "1.1")])
    payload = DigestPayload(digests=[d1, d2])
    summary = build_summary(payload)
    assert len(summary.lines) == 3
    projects = {l.project for l in summary.lines}
    assert projects == {"app1", "app2"}
