"""Unit tests for depwatch.cli_labeling."""
from __future__ import annotations

import argparse
import json
from unittest.mock import patch, MagicMock

import pytest

from depwatch.cli_labeling import add_label_parser, _run_label


def _make_namespace(**kwargs):
    defaults = {
        "config": "depwatch.yml",
        "security": [],
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_update(pkg="requests", current="1.0.0", latest="2.0.0"):
    u = MagicMock()
    u.package_name = pkg
    u.current_version = current
    u.latest_version = latest
    u.language = "python"
    u.project_name = "myapp"
    return u


def test_add_label_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_label_parser(sub)
    args = parser.parse_args(["label", "--format", "json"])
    assert args.format == "json"


def test_run_label_missing_config(tmp_path, capsys):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    with pytest.raises(SystemExit) as exc:
        _run_label(ns)
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_label_text_no_updates(tmp_path, capsys):
    cfg = MagicMock()
    with patch("depwatch.cli_labeling.load_config", return_value=cfg), \
         patch("depwatch.cli_labeling._collect_updates", return_value=[]):
        ns = _make_namespace(config="depwatch.yml")
        _run_label(ns)
    captured = capsys.readouterr()
    assert "No updates" in captured.out


def test_run_label_text_output(tmp_path, capsys):
    cfg = MagicMock()
    updates = [_make_update()]
    with patch("depwatch.cli_labeling.load_config", return_value=cfg), \
         patch("depwatch.cli_labeling._collect_updates", return_value=updates):
        ns = _make_namespace(config="depwatch.yml", format="text")
        _run_label(ns)
    captured = capsys.readouterr()
    assert "requests" in captured.out
    assert "->" in captured.out


def test_run_label_json_output(tmp_path, capsys):
    cfg = MagicMock()
    updates = [_make_update()]
    with patch("depwatch.cli_labeling.load_config", return_value=cfg), \
         patch("depwatch.cli_labeling._collect_updates", return_value=updates):
        ns = _make_namespace(config="depwatch.yml", format="json")
        _run_label(ns)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["package"] == "requests"
    assert "labels" in data[0]
