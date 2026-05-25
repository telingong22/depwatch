"""Unit tests for depwatch.cli_escalation."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_escalation import add_escalation_parser, _run_escalation
from depwatch.escalation import EscalatedUpdate, EscalationRule
from depwatch.checker import UpdateInfo


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "depwatch.yml",
        "min_days": 7,
        "major_only": False,
        "channel": "email",
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_escalation_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_escalation_parser(sub)
    args = parser.parse_args(["escalation", "--min-days", "3"])
    assert args.min_days == 3


def test_run_escalation_missing_config():
    ns = _make_namespace(config="/nonexistent/depwatch.yml")
    rc = _run_escalation(ns)
    assert rc == 1


def test_run_escalation_invalid_rule(tmp_path):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: p\n    path: .\n    language: python\n")
    ns = _make_namespace(config=str(cfg_file), min_days=0)
    rc = _run_escalation(ns)
    assert rc == 1


def test_run_escalation_text_no_results(tmp_path, capsys):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: p\n    path: .\n    language: python\n")
    ns = _make_namespace(config=str(cfg_file))
    with patch("depwatch.cli_escalation.load_state", return_value={}), \
         patch("depwatch.cli_escalation._collect_updates", return_value={}), \
         patch("depwatch.cli_escalation.build_all_digests", return_value=[]), \
         patch("depwatch.cli_escalation.escalate_all", return_value=[]):
        rc = _run_escalation(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No escalations" in out


def test_run_escalation_text_with_results(tmp_path, capsys):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: p\n    path: .\n    language: python\n")
    rule = EscalationRule(min_overdue_days=7, channel="email")
    u = UpdateInfo(package="requests", current="1.0.0", latest="2.0.0",
                   language="python", first_seen=None)
    escalated = [EscalatedUpdate(project="p", update=u, rule=rule, overdue_days=10)]
    ns = _make_namespace(config=str(cfg_file))
    with patch("depwatch.cli_escalation.load_state", return_value={}), \
         patch("depwatch.cli_escalation._collect_updates", return_value={}), \
         patch("depwatch.cli_escalation.build_all_digests", return_value=[]), \
         patch("depwatch.cli_escalation.escalate_all", return_value=escalated):
        rc = _run_escalation(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "requests" in out
    assert "10" in out


def test_run_escalation_json_output(tmp_path, capsys):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text("projects:\n  - name: p\n    path: .\n    language: python\n")
    rule = EscalationRule(min_overdue_days=7, channel="slack")
    u = UpdateInfo(package="flask", current="2.0.0", latest="3.0.0",
                   language="python", first_seen=None)
    escalated = [EscalatedUpdate(project="p", update=u, rule=rule, overdue_days=8)]
    ns = _make_namespace(config=str(cfg_file), format="json")
    with patch("depwatch.cli_escalation.load_state", return_value={}), \
         patch("depwatch.cli_escalation._collect_updates", return_value={}), \
         patch("depwatch.cli_escalation.build_all_digests", return_value=[]), \
         patch("depwatch.cli_escalation.escalate_all", return_value=escalated):
        rc = _run_escalation(ns)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["package"] == "flask"
    assert data[0]["channel"] == "slack"
