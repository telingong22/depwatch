"""Unit tests for depwatch.cli_recommendations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from depwatch.cli_recommendations import add_recommendations_parser, _run_recommendations
from depwatch.recommendations import Recommendation, RecommendationReport


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "depwatch.yml",
        "format": "text",
        "priority": "all",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_recommendations_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_recommendations_parser(sub)
    args = parser.parse_args(["recommendations", "--format", "json"])
    assert args.format == "json"


def test_run_recommendations_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    result = _run_recommendations(ns)
    assert result == 1


def test_run_recommendations_text_no_results(tmp_path, capsys):
    cfg = tmp_path / "depwatch.yml"
    cfg.write_text("projects: []\nalerts:\n  email:\n    to: a@b.com\n    interval: 1h\n")
    ns = _make_namespace(config=str(cfg))
    empty_report = RecommendationReport()
    with patch("depwatch.cli_recommendations.Config.from_file"), \
         patch("depwatch.cli_recommendations.build_all_digests", return_value=[]), \
         patch("depwatch.cli_recommendations.build_recommendations", return_value=empty_report):
        result = _run_recommendations(ns)
    assert result == 0
    out = capsys.readouterr().out
    assert "No recommendations" in out


def test_run_recommendations_text_with_results(tmp_path, capsys):
    cfg = tmp_path / "depwatch.yml"
    cfg.write_text("projects: []\n")
    ns = _make_namespace(config=str(cfg))
    rec = Recommendation("proj", "pkg", "1.0", "2.0", "major version bump", "high")
    report = RecommendationReport(items=[rec])
    with patch("depwatch.cli_recommendations.Config.from_file"), \
         patch("depwatch.cli_recommendations.build_all_digests", return_value=[]), \
         patch("depwatch.cli_recommendations.build_recommendations", return_value=report):
        result = _run_recommendations(ns)
    assert result == 0
    out = capsys.readouterr().out
    assert "HIGH" in out
    assert "pkg" in out


def test_run_recommendations_json_output(tmp_path, capsys):
    cfg = tmp_path / "depwatch.yml"
    cfg.write_text("projects: []\n")
    ns = _make_namespace(config=str(cfg), format="json")
    rec = Recommendation("proj", "pkg", "1.0", "2.0", "r", "high")
    report = RecommendationReport(items=[rec])
    with patch("depwatch.cli_recommendations.Config.from_file"), \
         patch("depwatch.cli_recommendations.build_all_digests", return_value=[]), \
         patch("depwatch.cli_recommendations.build_recommendations", return_value=report):
        result = _run_recommendations(ns)
    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total"] == 1
    assert data["items"][0]["package"] == "pkg"


def test_run_recommendations_priority_filter(tmp_path, capsys):
    cfg = tmp_path / "depwatch.yml"
    cfg.write_text("projects: []\n")
    ns = _make_namespace(config=str(cfg), priority="high")
    rec_high = Recommendation("p", "a", "1", "2", "r", "high")
    rec_low = Recommendation("p", "b", "1", "2", "r", "low")
    report = RecommendationReport(items=[rec_high, rec_low])
    with patch("depwatch.cli_recommendations.Config.from_file"), \
         patch("depwatch.cli_recommendations.build_all_digests", return_value=[]), \
         patch("depwatch.cli_recommendations.build_recommendations", return_value=report):
        _run_recommendations(ns)
    out = capsys.readouterr().out
    assert "a" in out
    assert "b" not in out
