"""Tests for depwatch.trending and depwatch.cli_trending."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from depwatch.trending import TrendEntry, TrendReport, build_trend_report
from depwatch.history import HistoryEntry


def _make_update(project: str, package: str, language: str = "python"):
    return SimpleNamespace(project=project, package=package, language=language,
                           current="1.0.0", latest="1.1.0")


def _make_entry(*updates) -> HistoryEntry:
    return HistoryEntry(timestamp="2024-01-01T00:00:00", updates=list(updates))


# ---------------------------------------------------------------------------
# TrendEntry
# ---------------------------------------------------------------------------

def test_trend_entry_to_dict_keys():
    e = TrendEntry(package="requests", project="myapp", language="python", update_count=3)
    d = e.to_dict()
    assert set(d.keys()) == {"package", "project", "language", "update_count"}


def test_trend_entry_str():
    e = TrendEntry(package="requests", project="myapp", language="python", update_count=3)
    assert "requests" in str(e)
    assert "3" in str(e)


# ---------------------------------------------------------------------------
# TrendReport
# ---------------------------------------------------------------------------

def test_trend_report_is_empty_when_no_entries():
    assert TrendReport().is_empty()


def test_trend_report_not_empty():
    e = TrendEntry(package="x", project="p", language="go", update_count=1)
    assert not TrendReport(entries=[e]).is_empty()


def test_trend_report_to_text_empty():
    assert "No trending" in TrendReport().to_text()


def test_trend_report_to_text_with_entries():
    e = TrendEntry(package="requests", project="myapp", language="python", update_count=4)
    text = TrendReport(entries=[e]).to_text()
    assert "requests" in text
    assert "4" in text


def test_trend_report_to_dict_structure():
    e = TrendEntry(package="x", project="p", language="python", update_count=2)
    d = TrendReport(entries=[e]).to_dict()
    assert "trending" in d
    assert d["trending"][0]["package"] == "x"


# ---------------------------------------------------------------------------
# build_trend_report
# ---------------------------------------------------------------------------

def test_build_trend_report_empty_history():
    report = build_trend_report([], top_n=5)
    assert report.is_empty()


def test_build_trend_report_top_n_limits_results():
    u1 = _make_update("proj", "alpha")
    u2 = _make_update("proj", "beta")
    u3 = _make_update("proj", "gamma")
    history = [_make_entry(u1, u2, u3), _make_entry(u1, u2), _make_entry(u1)]
    report = build_trend_report(history, top_n=2)
    assert len(report.entries) == 2


def test_build_trend_report_counts_correctly():
    u = _make_update("proj", "requests")
    history = [_make_entry(u), _make_entry(u), _make_entry(u)]
    report = build_trend_report(history, top_n=5)
    assert report.entries[0].update_count == 3
    assert report.entries[0].package == "requests"


def test_build_trend_report_invalid_top_n():
    with pytest.raises(ValueError):
        build_trend_report([], top_n=0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_add_trending_parser_registers_subcommand():
    from depwatch.cli_trending import add_trending_parser
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_trending_parser(sub)
    args = root.parse_args(["trending"])
    assert hasattr(args, "func")


def test_run_trending_missing_file(tmp_path):
    from depwatch.cli_trending import _run_trending
    ns = SimpleNamespace(history=str(tmp_path / "missing.json"), top=5, format="text")
    assert _run_trending(ns) == 1


def test_run_trending_text_output(tmp_path):
    from depwatch.cli_trending import _run_trending
    history_file = tmp_path / "history.json"
    u = _make_update("myapp", "requests")
    entry = _make_entry(u, u)
    with patch("depwatch.cli_trending.load_history", return_value=[entry]):
        ns = SimpleNamespace(history=str(history_file), top=5, format="text")
        history_file.write_text("[]")
        result = _run_trending(ns)
    assert result == 0
