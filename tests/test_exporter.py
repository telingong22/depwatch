"""Tests for depwatch.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.exporter import export_json, export_markdown, export_report
from depwatch.reporter import Report, build_report


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_update(pkg: str, current: str, latest: str) -> UpdateInfo:
    return UpdateInfo(package_name=pkg, current_version=current, latest_version=latest)


def _make_digest(project: str, *updates: UpdateInfo) -> ProjectDigest:
    return ProjectDigest(project_name=project, updates=list(updates))


def _report(*digests: ProjectDigest) -> Report:
    return build_report(list(digests))


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

def test_export_json_creates_file(tmp_path: Path) -> None:
    dest = tmp_path / "out" / "report.json"
    r = _report(_make_digest("proj", _make_update("requests", "2.28.0", "2.31.0")))
    export_json(r, dest)
    assert dest.exists()


def test_export_json_valid_structure(tmp_path: Path) -> None:
    dest = tmp_path / "report.json"
    r = _report(_make_digest("proj", _make_update("flask", "2.0.0", "3.0.0")))
    export_json(r, dest)
    data = json.loads(dest.read_text())
    assert "entries" in data
    assert data["entries"][0]["project_name"] == "proj"


def test_export_json_empty_report(tmp_path: Path) -> None:
    dest = tmp_path / "empty.json"
    export_json(_report(), dest)
    data = json.loads(dest.read_text())
    assert data["entries"] == []


# ---------------------------------------------------------------------------
# export_markdown
# ---------------------------------------------------------------------------

def test_export_markdown_creates_file(tmp_path: Path) -> None:
    dest = tmp_path / "report.md"
    r = _report(_make_digest("myapp", _make_update("httpx", "0.23.0", "0.27.0")))
    export_markdown(r, dest)
    assert dest.exists()


def test_export_markdown_contains_project_name(tmp_path: Path) -> None:
    dest = tmp_path / "report.md"
    r = _report(_make_digest("myapp", _make_update("httpx", "0.23.0", "0.27.0")))
    export_markdown(r, dest)
    assert "myapp" in dest.read_text()


def test_export_markdown_empty_report(tmp_path: Path) -> None:
    dest = tmp_path / "empty.md"
    export_markdown(_report(), dest)
    assert "No updates found" in dest.read_text()


def test_export_markdown_shows_versions(tmp_path: Path) -> None:
    dest = tmp_path / "report.md"
    r = _report(_make_digest("svc", _make_update("django", "4.1", "5.0")))
    export_markdown(r, dest)
    content = dest.read_text()
    assert "4.1" in content
    assert "5.0" in content


# ---------------------------------------------------------------------------
# export_report dispatch
# ---------------------------------------------------------------------------

def test_export_report_json(tmp_path: Path) -> None:
    dest = tmp_path / "r.json"
    export_report(_report(), "json", dest)
    assert dest.exists()


def test_export_report_markdown(tmp_path: Path) -> None:
    dest = tmp_path / "r.md"
    export_report(_report(), "markdown", dest)
    assert dest.exists()


def test_export_report_md_alias(tmp_path: Path) -> None:
    dest = tmp_path / "r.md"
    export_report(_report(), "md", dest)
    assert dest.exists()


def test_export_report_unknown_format(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_report(_report(), "csv", tmp_path / "r.csv")
