"""Unit tests for depwatch.cli_snapshot."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_snapshot import _run_snapshot, add_snapshot_parser
from depwatch.snapshot import Snapshot, SnapshotEntry


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "depwatch.yml",
        "output": ".depwatch_snapshot.json",
        "diff": False,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_snapshot_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_snapshot_parser(sub)
    args = parser.parse_args(["snapshot", "--diff"])
    assert args.diff is True


def test_run_snapshot_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    result = _run_snapshot(ns)
    assert result == 1


def test_run_snapshot_saves_file(tmp_path):
    output = str(tmp_path / "snap.json")
    ns = _make_namespace(output=output)

    mock_cfg = MagicMock()
    mock_cfg.projects = []

    with patch("depwatch.cli_snapshot.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_snapshot.parse_dependencies", return_value={}):
        result = _run_snapshot(ns)

    assert result == 0
    import os
    assert os.path.exists(output)


def test_run_snapshot_diff_text_no_changes(tmp_path, capsys):
    output = str(tmp_path / "snap.json")
    ns = _make_namespace(output=output, diff=True, format="text")

    mock_cfg = MagicMock()
    mock_cfg.projects = []

    existing = Snapshot(project="_all", entries=[])
    with patch("depwatch.cli_snapshot.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_snapshot.parse_dependencies", return_value={}), \
         patch("depwatch.cli_snapshot.load_snapshot", return_value=existing):
        result = _run_snapshot(ns)

    captured = capsys.readouterr()
    assert result == 0
    assert "No changes" in captured.out


def test_run_snapshot_diff_json_with_changes(tmp_path, capsys):
    output = str(tmp_path / "snap.json")
    ns = _make_namespace(output=output, diff=True, format="json")

    mock_project = MagicMock()
    mock_project.name = "myapp"
    mock_cfg = MagicMock()
    mock_cfg.projects = [mock_project]

    old_snap = Snapshot(
        project="_all",
        entries=[SnapshotEntry(package="myapp/requests", version="2.28.0")],
    )

    with patch("depwatch.cli_snapshot.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_snapshot.parse_dependencies", return_value={"requests": "2.31.0"}), \
         patch("depwatch.cli_snapshot.load_snapshot", return_value=old_snap):
        result = _run_snapshot(ns)

    captured = capsys.readouterr()
    assert result == 0
    data = json.loads(captured.out)
    assert "myapp/requests" in data
    assert data["myapp/requests"]["to"] == "2.31.0"
