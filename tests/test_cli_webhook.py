"""Unit tests for depwatch.cli_webhook."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from depwatch.cli_webhook import _run_webhook, add_webhook_parser


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "depwatch.yml",
        "url": "https://example.com/hook",
        "secret": None,
        "timeout": 10,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_webhook_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_webhook_parser(sub)
    ns = parser.parse_args(["webhook", "--url", "https://example.com"])
    assert hasattr(ns, "func")


def test_run_webhook_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    result = _run_webhook(ns)
    assert result == 1


def test_run_webhook_invalid_url(tmp_path):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text(
        "projects:\n  - name: myapp\n    language: python\n    path: .\n"
        "alert:\n  target: test@example.com\n  interval: 1h\n"
    )
    ns = _make_namespace(config=str(cfg_file), url="ftp://bad")
    result = _run_webhook(ns)
    assert result == 1


def test_run_webhook_success(tmp_path):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text(
        "projects:\n  - name: myapp\n    language: python\n    path: .\n"
        "alert:\n  target: test@example.com\n  interval: 1h\n"
    )
    ns = _make_namespace(config=str(cfg_file))
    with patch("depwatch.cli_webhook.send_webhook", return_value=True):
        result = _run_webhook(ns)
    assert result == 0


def test_run_webhook_delivery_failure(tmp_path):
    cfg_file = tmp_path / "depwatch.yml"
    cfg_file.write_text(
        "projects:\n  - name: myapp\n    language: python\n    path: .\n"
        "alert:\n  target: test@example.com\n  interval: 1h\n"
    )
    ns = _make_namespace(config=str(cfg_file))
    with patch("depwatch.cli_webhook.send_webhook", return_value=False):
        result = _run_webhook(ns)
    assert result == 2
