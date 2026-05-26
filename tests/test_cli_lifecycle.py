"""Unit tests for depwatch.cli_lifecycle."""
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_lifecycle import _run_lifecycle, add_lifecycle_parser
from depwatch.lifecycle import LifecycleEntry


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = dict(
        config="depwatch.yml",
        state=".depwatch_state.json",
        lifecycle_file=".depwatch_lifecycle.json",
        format="text",
        stage_filter="all",
        set_stage=None,
        note="",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_entry(pkg="requests", stage="new") -> LifecycleEntry:
    return LifecycleEntry(
        project="myapp", package=pkg,
        current_version="1.0", latest_version="2.0",
        stage=stage, created_at="t", updated_at="t",
    )


def test_add_lifecycle_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_lifecycle_parser(sub)
    args = parser.parse_args(["lifecycle", "--format", "json"])
    assert args.format == "json"


def test_run_lifecycle_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    result = _run_lifecycle(ns)
    assert result == 1


def test_run_lifecycle_text_empty(tmp_path, capsys):
    ns = _make_namespace(
        config=str(tmp_path / "cfg.yml"),
        lifecycle_file=str(tmp_path / "lc.json"),
    )
    mock_cfg = MagicMock()
    with patch("depwatch.cli_lifecycle.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_lifecycle.load_lifecycle", return_value={}):
        result = _run_lifecycle(ns)
    assert result == 0
    captured = capsys.readouterr()
    assert "No lifecycle entries" in captured.out


def test_run_lifecycle_json_output(tmp_path, capsys):
    ns = _make_namespace(
        config=str(tmp_path / "cfg.yml"),
        lifecycle_file=str(tmp_path / "lc.json"),
        format="json",
    )
    entry = _make_entry()
    mock_cfg = MagicMock()
    with patch("depwatch.cli_lifecycle.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_lifecycle.load_lifecycle", return_value={"k": entry}):
        result = _run_lifecycle(ns)
    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["package"] == "requests"


def test_run_lifecycle_set_stage(tmp_path):
    ns = _make_namespace(
        config=str(tmp_path / "cfg.yml"),
        lifecycle_file=str(tmp_path / "lc.json"),
        set_stage="active",
        note="reviewing",
    )
    from depwatch.checker import UpdateInfo
    fake_update = UpdateInfo(
        project_name="myapp", package="requests",
        current_version="1.0", latest_version="2.0", language="python",
    )
    mock_cfg = MagicMock()
    with patch("depwatch.cli_lifecycle.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_lifecycle.load_lifecycle", return_value={}), \
         patch("depwatch.cli_lifecycle._collect_updates", return_value=[fake_update]), \
         patch("depwatch.cli_lifecycle.save_lifecycle") as mock_save:
        result = _run_lifecycle(ns)
    assert result == 0
    mock_save.assert_called_once()
