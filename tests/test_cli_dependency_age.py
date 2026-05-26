"""Tests for depwatch.cli_dependency_age."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from depwatch.cli_dependency_age import _run_age, add_age_parser
from depwatch.dependency_age import AgeEntry, AgeReport


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"config": "depwatch.yml", "format": "text", "min_days": 0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _iso(days_ago: int) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _make_entry(package: str = "requests", age: int = 10) -> AgeEntry:
    return AgeEntry(
        project="proj",
        package=package,
        language="python",
        current_version="1.0.0",
        latest_version="1.1.0",
        published_at=_iso(age),
        age_days=age,
    )


def test_add_age_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_age_parser(sub)
    ns = parser.parse_args(["age", "--config", "x.yml"])
    assert ns.config == "x.yml"


def test_run_age_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    result = _run_age(ns)
    assert result == 1


@patch("depwatch.cli_dependency_age.load_config")
@patch("depwatch.cli_dependency_age.load_state")
@patch("depwatch.cli_dependency_age._collect_updates")
@patch("depwatch.cli_dependency_age.build_all_digests")
@patch("depwatch.cli_dependency_age.build_age_report")
def test_run_age_text_no_results(
    mock_report, mock_digests, mock_updates, mock_state, mock_cfg, capsys
):
    mock_cfg.return_value = MagicMock(projects=[])
    mock_state.return_value = {}
    mock_updates.return_value = []
    mock_digests.return_value = []
    mock_report.return_value = AgeReport(entries=[])

    ns = _make_namespace()
    result = _run_age(ns)
    assert result == 0
    out = capsys.readouterr().out
    assert "No dependency" in out


@patch("depwatch.cli_dependency_age.load_config")
@patch("depwatch.cli_dependency_age.load_state")
@patch("depwatch.cli_dependency_age._collect_updates")
@patch("depwatch.cli_dependency_age.build_all_digests")
@patch("depwatch.cli_dependency_age.build_age_report")
def test_run_age_json_output(
    mock_report, mock_digests, mock_updates, mock_state, mock_cfg, capsys
):
    mock_cfg.return_value = MagicMock(projects=[])
    mock_state.return_value = {}
    mock_updates.return_value = []
    mock_digests.return_value = []
    mock_report.return_value = AgeReport(entries=[_make_entry()])

    ns = _make_namespace(format="json")
    result = _run_age(ns)
    assert result == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert data["entries"][0]["package"] == "requests"


@patch("depwatch.cli_dependency_age.load_config")
@patch("depwatch.cli_dependency_age.load_state")
@patch("depwatch.cli_dependency_age._collect_updates")
@patch("depwatch.cli_dependency_age.build_all_digests")
@patch("depwatch.cli_dependency_age.build_age_report")
def test_run_age_min_days_filter(
    mock_report, mock_digests, mock_updates, mock_state, mock_cfg, capsys
):
    mock_cfg.return_value = MagicMock(projects=[])
    mock_state.return_value = {}
    mock_updates.return_value = []
    mock_digests.return_value = []
    mock_report.return_value = AgeReport(
        entries=[_make_entry("old", 50), _make_entry("new", 2)]
    )

    ns = _make_namespace(min_days=10)
    result = _run_age(ns)
    assert result == 0
    out = capsys.readouterr().out
    assert "old" in out
    assert "new" not in out
