"""Tests for depwatch.cli_alert."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_alert import add_alert_parser, _run_alert
from depwatch.alerting import AlertDecision
from depwatch.digest import ProjectDigest


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = dict(
        config="depwatch.yml",
        min_updates=1,
        require_major=False,
        fmt="text",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_alert_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_alert_parser(sub)
    args = root.parse_args(["alert", "--min-updates", "2"])
    assert args.min_updates == 2


def test_run_alert_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    rc = _run_alert(ns)
    assert rc == 1


def test_run_alert_text_suppress(tmp_path, capsys):
    decision = AlertDecision(
        should_alert=False,
        reason="only 0 update(s), need 1",
        digests=[],
    )
    with patch("depwatch.cli_alert.load_config") as lc, \
         patch("depwatch.cli_alert.load_state", return_value={}), \
         patch("depwatch.cli_alert._collect_updates", return_value={}), \
         patch("depwatch.cli_alert.build_all_digests", return_value=[]), \
         patch("depwatch.cli_alert.evaluate_threshold", return_value=decision):
        lc.return_value = MagicMock(spec=["state_file"])
        ns = _make_namespace(fmt="text")
        rc = _run_alert(ns)

    assert rc == 2
    out = capsys.readouterr().out
    assert "SUPPRESS" in out


def test_run_alert_text_alert(capsys):
    digest = ProjectDigest(project="myapp", updates=[MagicMock()])
    decision = AlertDecision(should_alert=True, reason="1 update(s) passed", digests=[digest])
    with patch("depwatch.cli_alert.load_config") as lc, \
         patch("depwatch.cli_alert.load_state", return_value={}), \
         patch("depwatch.cli_alert._collect_updates", return_value={}), \
         patch("depwatch.cli_alert.build_all_digests", return_value=[]), \
         patch("depwatch.cli_alert.evaluate_threshold", return_value=decision):
        lc.return_value = MagicMock(spec=["state_file"])
        rc = _run_alert(_make_namespace())

    assert rc == 0
    out = capsys.readouterr().out
    assert "ALERT" in out


def test_run_alert_json_format(capsys):
    decision = AlertDecision(should_alert=True, reason="2 update(s) passed", digests=[])
    with patch("depwatch.cli_alert.load_config") as lc, \
         patch("depwatch.cli_alert.load_state", return_value={}), \
         patch("depwatch.cli_alert._collect_updates", return_value={}), \
         patch("depwatch.cli_alert.build_all_digests", return_value=[]), \
         patch("depwatch.cli_alert.evaluate_threshold", return_value=decision):
        lc.return_value = MagicMock(spec=["state_file"])
        rc = _run_alert(_make_namespace(fmt="json"))

    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["should_alert"] is True
    assert "reason" in data
    assert "projects" in data
