"""Tests for depwatch.cli_filter."""
from __future__ import annotations

import argparse
import types
from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import UpdateInfo
from depwatch.cli_filter import _run_filter, add_filter_parser


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "depwatch.yml",
        "ignore": [],
        "min_bump": "patch",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_update(pkg: str, current: str, latest: str) -> UpdateInfo:
    return UpdateInfo(package=pkg, current_version=current, latest_version=latest)


def test_add_filter_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_filter_parser(sub)
    args = parser.parse_args(["filter", "--config", "x.yml"])
    assert args.config == "x.yml"


def test_run_filter_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    rc = _run_filter(ns)
    assert rc == 1


def test_run_filter_no_updates(tmp_path, capsys):
    cfg_path = tmp_path / "depwatch.yml"
    cfg_path.write_text("")
    ns = _make_namespace(config=str(cfg_path))

    fake_cfg = MagicMock()
    with patch("depwatch.cli_filter.load_config", return_value=fake_cfg), \
         patch("depwatch.cli_filter._collect_updates", return_value=[]):
        rc = _run_filter(ns)

    assert rc == 0
    out = capsys.readouterr().out
    assert "No pending updates" in out


def test_run_filter_all_pass(tmp_path, capsys):
    ns = _make_namespace(config="depwatch.yml", min_bump="patch")
    updates = [_make_update("requests", "2.27.0", "2.28.0")]
    fake_cfg = MagicMock()

    with patch("depwatch.cli_filter.load_config", return_value=fake_cfg), \
         patch("depwatch.cli_filter._collect_updates", return_value=updates):
        rc = _run_filter(ns)

    assert rc == 0
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "requests" in out


def test_run_filter_suppressed_shown(tmp_path, capsys):
    ns = _make_namespace(config="depwatch.yml", ignore=["boto3"], min_bump="patch")
    updates = [
        _make_update("boto3", "1.0.0", "2.0.0"),
        _make_update("requests", "2.27.0", "2.28.0"),
    ]
    fake_cfg = MagicMock()

    with patch("depwatch.cli_filter.load_config", return_value=fake_cfg), \
         patch("depwatch.cli_filter._collect_updates", return_value=updates):
        rc = _run_filter(ns)

    assert rc == 0
    out = capsys.readouterr().out
    assert "SUPPRESSED" in out
    assert "boto3" in out
