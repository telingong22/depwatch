"""Tests for depwatch.heatmap and depwatch.cli_heatmap."""
from __future__ import annotations

import argparse
import json
from unittest.mock import patch, MagicMock

import pytest

from depwatch.heatmap import HeatmapEntry, HeatmapReport, build_heatmap
from depwatch.cli_heatmap import add_heatmap_parser, _run_heatmap


def _make_update(project: str, package: str, language: str = "python"):
    u = MagicMock()
    u.project_name = project
    u.package_name = package
    u.language = language
    return u


def _make_entry(updates):
    e = MagicMock()
    e.updates = updates
    return e


# --- HeatmapEntry ---

def test_heatmap_entry_to_dict_keys():
    e = HeatmapEntry(package="requests", language="python", project="svc", update_count=3)
    d = e.to_dict()
    assert set(d.keys()) == {"package", "language", "project", "update_count"}


def test_heatmap_entry_to_dict_values():
    e = HeatmapEntry(package="requests", language="python", project="svc", update_count=3)
    d = e.to_dict()
    assert d["package"] == "requests"
    assert d["update_count"] == 3


def test_heatmap_entry_str_contains_package():
    e = HeatmapEntry(package="flask", language="python", project="api", update_count=5)
    assert "flask" in str(e)
    assert "5" in str(e)


# --- HeatmapReport ---

def test_heatmap_report_is_empty_when_no_entries():
    assert HeatmapReport().is_empty()


def test_heatmap_report_not_empty_with_entries():
    e = HeatmapEntry(package="x", language="python", project="p", update_count=1)
    assert not HeatmapReport(entries=[e]).is_empty()


def test_heatmap_report_top_limits_results():
    entries = [HeatmapEntry(package=f"pkg{i}", language="python", project="p", update_count=i) for i in range(20)]
    report = HeatmapReport(entries=entries)
    assert len(report.top(5)) == 5


def test_heatmap_report_to_dict_has_entries_key():
    report = HeatmapReport()
    assert "entries" in report.to_dict()


# --- build_heatmap ---

def test_build_heatmap_empty_history():
    report = build_heatmap([])
    assert report.is_empty()


def test_build_heatmap_counts_correctly():
    u1 = _make_update("proj", "requests")
    u2 = _make_update("proj", "requests")
    u3 = _make_update("proj", "flask")
    history = [_make_entry([u1, u3]), _make_entry([u2])]
    report = build_heatmap(history)
    counts = {e.package: e.update_count for e in report.entries}
    assert counts["requests"] == 2
    assert counts["flask"] == 1


def test_build_heatmap_sorted_by_frequency():
    entries = [
        _make_entry([_make_update("p", "rare")]),
        _make_entry([_make_update("p", "common"), _make_update("p", "common")]),
    ]
    report = build_heatmap(entries)
    assert report.entries[0].package == "common"


# --- CLI ---

def test_add_heatmap_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_heatmap_parser(sub)
    args = parser.parse_args(["heatmap"])
    assert hasattr(args, "func")


def test_run_heatmap_empty_history(tmp_path):
    ns = argparse.Namespace(history_file=str(tmp_path / "missing.json"), top=10, fmt="text")
    with patch("depwatch.cli_heatmap.load_history", return_value=[]):
        rc = _run_heatmap(ns)
    assert rc == 0


def test_run_heatmap_json_output(tmp_path, capsys):
    u = _make_update("proj", "requests")
    entry = _make_entry([u])
    ns = argparse.Namespace(history_file="h.json", top=10, fmt="json")
    with patch("depwatch.cli_heatmap.load_history", return_value=[entry]):
        rc = _run_heatmap(ns)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert rc == 0
