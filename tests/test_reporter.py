"""Tests for depwatch.reporter."""

from __future__ import annotations

import json
import os

import pytest

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.reporter import (
    Report,
    ReportEntry,
    build_report,
    format_report_text,
    write_report,
)


def _make_digest(project: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=project, updates=updates)


def _make_update(pkg: str, current: str, latest: str, published: str = "") -> UpdateInfo:
    return UpdateInfo(
        package=pkg,
        current_version=current,
        latest_version=latest,
        published_at=published or None,
    )


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

def test_report_is_empty_when_no_entries():
    report = Report()
    assert report.is_empty()


def test_report_not_empty_with_entries():
    report = Report(entries=[ReportEntry("p", "pkg", "1.0", "2.0", "")])
    assert not report.is_empty()


def test_report_to_dict_structure():
    entry = ReportEntry("myproject", "requests", "2.28.0", "2.31.0", "2024-01-01")
    report = Report(generated_at="2024-06-01T00:00:00+00:00", entries=[entry])
    d = report.to_dict()
    assert d["generated_at"] == "2024-06-01T00:00:00+00:00"
    assert len(d["entries"]) == 1
    assert d["entries"][0]["package"] == "requests"
    assert d["entries"][0]["latest_version"] == "2.31.0"


# ---------------------------------------------------------------------------
# build_report
# ---------------------------------------------------------------------------

def test_build_report_empty_digests():
    report = build_report([])
    assert report.is_empty()


def test_build_report_single_digest():
    digest = _make_digest("myapp", [_make_update("flask", "2.0.0", "3.0.0", "2024-03-01")])
    report = build_report([digest])
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.project == "myapp"
    assert entry.package == "flask"
    assert entry.current_version == "2.0.0"
    assert entry.latest_version == "3.0.0"
    assert entry.published_at == "2024-03-01"


def test_build_report_multiple_digests():
    d1 = _make_digest("svc-a", [_make_update("boto3", "1.0", "1.1")])
    d2 = _make_digest("svc-b", [_make_update("gin", "1.8.0", "1.9.0"), _make_update("zap", "1.19.0", "1.21.0")])
    report = build_report([d1, d2])
    assert len(report.entries) == 3
    projects = [e.project for e in report.entries]
    assert projects.count("svc-a") == 1
    assert projects.count("svc-b") == 2


# ---------------------------------------------------------------------------
# write_report
# ---------------------------------------------------------------------------

def test_write_report_creates_file(tmp_path):
    report = build_report(
        [_make_digest("proj", [_make_update("httpx", "0.23", "0.27")])]
    )
    out = str(tmp_path / "reports" / "out.json")
    write_report(report, out)
    assert os.path.exists(out)
    with open(out, encoding="utf-8") as fh:
        data = json.load(fh)
    assert len(data["entries"]) == 1
    assert data["entries"][0]["package"] == "httpx"


def test_write_report_valid_json(tmp_path):
    report = Report()
    out = str(tmp_path / "empty.json")
    write_report(report, out)
    with open(out, encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["entries"] == []


# ---------------------------------------------------------------------------
# format_report_text
# ---------------------------------------------------------------------------

def test_format_report_text_empty():
    report = Report()
    text = format_report_text(report)
    assert "No dependency updates" in text


def test_format_report_text_contains_package():
    digest = _make_digest("api", [_make_update("pydantic", "1.10", "2.7", "2024-05-01")])
    report = build_report([digest])
    text = format_report_text(report)
    assert "pydantic" in text
    assert "1.10" in text
    assert "2.7" in text
    assert "2024-05-01" in text


def test_format_report_text_no_published_date():
    digest = _make_digest("api", [_make_update("click", "7.0", "8.1")])
    report = build_report([digest])
    text = format_report_text(report)
    assert "click" in text
    assert "released" not in text
