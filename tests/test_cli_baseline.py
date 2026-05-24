"""Unit tests for depwatch.cli_baseline."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_baseline import _run_baseline, add_baseline_parser


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "depwatch.yml",
        "file": "baseline.json",
        "action": "capture",
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_baseline_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_baseline_parser(sub)
    args = root.parse_args(["baseline", "--action", "capture"])
    assert args.action == "capture"


def test_run_baseline_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    rc = _run_baseline(ns)
    assert rc == 1


def test_run_baseline_capture_writes_file(tmp_path):
    mock_cfg = MagicMock()
    proj = MagicMock()
    proj.name = "myapp"
    mock_cfg.projects = [proj]

    baseline_file = str(tmp_path / "baseline.json")
    ns = _make_namespace(file=baseline_file, action="capture")

    with patch("depwatch.cli_baseline.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_baseline.parse_dependencies", return_value={"requests": "2.31.0"}):
        rc = _run_baseline(ns)

    assert rc == 0
    with open(baseline_file) as fh:
        data = json.load(fh)
    assert any(d["package"] == "requests" for d in data)


def test_run_baseline_diff_text_no_changes(tmp_path, capsys):
    from depwatch.baseline import BaselineEntry, save_baseline

    baseline_file = str(tmp_path / "baseline.json")
    save_baseline(baseline_file, [BaselineEntry("requests", "2.31.0", "myapp")])

    mock_cfg = MagicMock()
    proj = MagicMock()
    proj.name = "myapp"
    mock_cfg.projects = [proj]

    ns = _make_namespace(file=baseline_file, action="diff", format="text")
    with patch("depwatch.cli_baseline.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_baseline.parse_dependencies", return_value={"requests": "2.31.0"}):
        rc = _run_baseline(ns)

    assert rc == 0
    out = capsys.readouterr().out
    assert "No changes" in out


def test_run_baseline_diff_json_output(tmp_path, capsys):
    from depwatch.baseline import BaselineEntry, save_baseline

    baseline_file = str(tmp_path / "baseline.json")
    save_baseline(baseline_file, [BaselineEntry("requests", "2.28.0", "myapp")])

    mock_cfg = MagicMock()
    proj = MagicMock()
    proj.name = "myapp"
    mock_cfg.projects = [proj]

    ns = _make_namespace(file=baseline_file, action="diff", format="json")
    with patch("depwatch.cli_baseline.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_baseline.parse_dependencies", return_value={"requests": "2.31.0"}):
        rc = _run_baseline(ns)

    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "myapp/requests" in data
