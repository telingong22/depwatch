"""Tests for depwatch.cli_export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_export import _run_export, add_export_parser
from depwatch.reporter import Report


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _empty_report() -> Report:
    return Report(entries=[])


def _make_namespace(**kwargs) -> argparse.Namespace:  # type: ignore[return]
    defaults = dict(config="depwatch.yml", fmt="json", output="/tmp/out.json")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# add_export_parser
# ---------------------------------------------------------------------------

def test_add_export_parser_registers_subcommand() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_export_parser(sub)
    args = parser.parse_args(["export", "--output", "r.json"])
    assert hasattr(args, "func")


# ---------------------------------------------------------------------------
# _run_export
# ---------------------------------------------------------------------------

def test_run_export_missing_config(tmp_path: Path) -> None:
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    rc = _run_export(ns)
    assert rc == 1


def test_run_export_writes_json(tmp_path: Path) -> None:
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: test\n    path: .\n    language: python\nalerts:\n  target: x@x.com\n")
    out = tmp_path / "report.json"

    mock_cfg = MagicMock()
    mock_report = _empty_report()

    with patch("depwatch.cli_export.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_export.runner_run_once", return_value=mock_report):
        ns = _make_namespace(config=str(cfg_file), fmt="json", output=str(out))
        rc = _run_export(ns)

    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "entries" in data


def test_run_export_writes_markdown(tmp_path: Path) -> None:
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: p\n    path: .\n    language: python\nalerts:\n  target: a@b.com\n")
    out = tmp_path / "report.md"

    mock_cfg = MagicMock()
    mock_report = _empty_report()

    with patch("depwatch.cli_export.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_export.runner_run_once", return_value=mock_report):
        ns = _make_namespace(config=str(cfg_file), fmt="markdown", output=str(out))
        rc = _run_export(ns)

    assert rc == 0
    assert out.exists()


def test_run_export_returns_zero_on_success(tmp_path: Path) -> None:
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects: []\nalerts:\n  target: a@b.com\n")
    out = tmp_path / "r.json"

    with patch("depwatch.cli_export.load_config", return_value=MagicMock()), \
         patch("depwatch.cli_export.runner_run_once", return_value=_empty_report()):
        rc = _run_export(_make_namespace(config=str(cfg_file), output=str(out)))

    assert rc == 0
