"""Unit tests for depwatch.cli_pinning."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_pinning import _run_pin, add_pin_parser
from depwatch.pinning import PinSuggestion


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"config": "depwatch.yml", "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_pin_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_pin_parser(sub)
    args = parser.parse_args(["pin", "--format", "json"])
    assert args.format == "json"


def test_run_pin_missing_config(tmp_path):
    args = _make_namespace(config=str(tmp_path / "missing.yml"))
    with pytest.raises(SystemExit) as exc:
        _run_pin(args)
    assert exc.value.code == 1


def test_run_pin_text_output_no_updates(tmp_path, capsys):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: p\n    language: python\n    path: .\nalerts:\n  target: x@x.com\n")

    with (
        patch("depwatch.cli_pinning.load_config") as mock_cfg,
        patch("depwatch.cli_pinning._collect_updates", return_value=[]),
        patch("depwatch.cli_pinning.build_all_digests", return_value=[]),
        patch("depwatch.cli_pinning.build_pin_suggestions", return_value=[]),
    ):
        mock_cfg.return_value = MagicMock()
        args = _make_namespace(config=str(cfg_file), format="text")
        _run_pin(args)

    captured = capsys.readouterr()
    assert "up to date" in captured.out


def test_run_pin_json_output(tmp_path, capsys):
    suggestion = PinSuggestion(
        project="proj", package="requests", language="python",
        current="2.28.0", suggested_pin="requests==2.31.0",
    )

    with (
        patch("depwatch.cli_pinning.load_config") as mock_cfg,
        patch("depwatch.cli_pinning._collect_updates", return_value=[]),
        patch("depwatch.cli_pinning.build_all_digests", return_value=[]),
        patch("depwatch.cli_pinning.build_pin_suggestions", return_value=[suggestion]),
    ):
        mock_cfg.return_value = MagicMock()
        cfg_file = tmp_path / "depwatch.yml"
        cfg_file.write_text("")
        args = _make_namespace(config=str(cfg_file), format="json")
        _run_pin(args)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["suggested_pin"] == "requests==2.31.0"
