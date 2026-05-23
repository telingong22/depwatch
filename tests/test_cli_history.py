"""Tests for depwatch.cli_history."""

import argparse
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from depwatch.cli_history import add_history_parser, _run_history
from depwatch.history import HistoryEntry


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_namespace(**kwargs):
    defaults = dict(
        history_file=".depwatch_history.json",
        project=None,
        package=None,
        as_json=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_entry(**kwargs) -> HistoryEntry:
    defaults = dict(
        project="myapp",
        package="requests",
        language="python",
        from_version="2.28.0",
        to_version="2.31.0",
        detected_at="2024-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    return HistoryEntry(**defaults)


_ENTRIES = [
    _make_entry(project="myapp", package="requests"),
    _make_entry(project="myapp", package="flask", from_version="2.0.0", to_version="3.0.0"),
    _make_entry(project="other", package="requests"),
]


# ---------------------------------------------------------------------------
# parser registration
# ---------------------------------------------------------------------------

def test_add_history_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_history_parser(sub)
    ns = root.parse_args(["history"])
    assert hasattr(ns, "func")


# ---------------------------------------------------------------------------
# _run_history
# ---------------------------------------------------------------------------

def test_run_history_empty(capsys):
    with patch("depwatch.cli_history.load_history", return_value=[]):
        rc = _run_history(_make_namespace())
    assert rc == 0
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_run_history_text_output(capsys):
    with patch("depwatch.cli_history.load_history", return_value=_ENTRIES):
        rc = _run_history(_make_namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "requests" in out
    assert "flask" in out


def test_run_history_json_output(capsys):
    with patch("depwatch.cli_history.load_history", return_value=_ENTRIES):
        rc = _run_history(_make_namespace(as_json=True))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == len(_ENTRIES)


def test_run_history_filter_project(capsys):
    with patch("depwatch.cli_history.load_history", return_value=_ENTRIES):
        rc = _run_history(_make_namespace(project="myapp", as_json=True))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert all(e["project"] == "myapp" for e in data)
    assert len(data) == 2


def test_run_history_filter_package(capsys):
    with patch("depwatch.cli_history.load_history", return_value=_ENTRIES):
        rc = _run_history(_make_namespace(package="requests", as_json=True))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert all(e["package"] == "requests" for e in data)
    assert len(data) == 2
