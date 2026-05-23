"""Unit tests for depwatch.cli_retention."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from depwatch.cli_retention import add_retention_parser, _run_retention
from depwatch.history import HistoryEntry


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"history": "depwatch_history.json", "max_days": 90, "func": _run_retention}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_history(path: str, days_ago_list):
    entries = []
    for d in days_ago_list:
        ts = datetime.now(tz=timezone.utc) - timedelta(days=d)
        e = HistoryEntry(project="p", package="pkg", previous="1.0", latest="1.1", timestamp=ts)
        entries.append(e.to_dict())
    with open(path, "w") as f:
        json.dump(entries, f)


def test_add_retention_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_retention_parser(sub)
    ns = root.parse_args(["prune", "--max-days", "30"])
    assert ns.max_days == 30
    assert ns.func is _run_retention


def test_run_retention_missing_file(tmp_path, capsys):
    args = _make_namespace(history=str(tmp_path / "no.json"))
    with pytest.raises(SystemExit) as exc:
        _run_retention(args)
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_retention_invalid_policy(tmp_path, capsys):
    path = str(tmp_path / "h.json")
    _write_history(path, [1])
    args = _make_namespace(history=path, max_days=0)
    with pytest.raises(SystemExit) as exc:
        _run_retention(args)
    assert exc.value.code == 1


def test_run_retention_prunes_old(tmp_path, capsys):
    path = str(tmp_path / "h.json")
    _write_history(path, [5, 200])
    args = _make_namespace(history=path, max_days=60)
    _run_retention(args)
    captured = capsys.readouterr()
    assert "Pruned 1" in captured.out


def test_run_retention_nothing_to_prune(tmp_path, capsys):
    path = str(tmp_path / "h.json")
    _write_history(path, [1, 2])
    args = _make_namespace(history=path, max_days=30)
    _run_retention(args)
    captured = capsys.readouterr()
    assert "Nothing to prune" in captured.out
