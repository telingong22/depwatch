"""Unit tests for depwatch.cli_coupling."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

from depwatch.cli_coupling import add_coupling_parser, _run_coupling
from depwatch.coupling import CoupledPackage, CouplingReport


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"config": "depwatch.yml", "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_coupling_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_coupling_parser(sub)
    ns = parser.parse_args(["coupling"])
    assert hasattr(ns, "func")


def test_run_coupling_missing_config(tmp_path):
    ns = _make_namespace(config=str(tmp_path / "missing.yml"))
    result = _run_coupling(ns)
    assert result == 1


def test_run_coupling_text_empty(tmp_path, capsys):
    empty_report = CouplingReport(coupled=[])
    with patch("depwatch.cli_coupling.Config") as MockConfig, \
         patch("depwatch.cli_coupling._collect_updates", return_value={}), \
         patch("depwatch.cli_coupling.build_all_digests", return_value=[]), \
         patch("depwatch.cli_coupling.build_coupling_report", return_value=empty_report):
        MockConfig.from_file.return_value = MagicMock()
        ns = _make_namespace(format="text")
        result = _run_coupling(ns)

    captured = capsys.readouterr()
    assert result == 0
    assert "No coupled" in captured.out


def test_run_coupling_text_with_results(tmp_path, capsys):
    cp = CoupledPackage("requests", "python", ["proj-a", "proj-b"], "2.28.0")
    report = CouplingReport(coupled=[cp])
    with patch("depwatch.cli_coupling.Config") as MockConfig, \
         patch("depwatch.cli_coupling._collect_updates", return_value={}), \
         patch("depwatch.cli_coupling.build_all_digests", return_value=[]), \
         patch("depwatch.cli_coupling.build_coupling_report", return_value=report):
        MockConfig.from_file.return_value = MagicMock()
        ns = _make_namespace(format="text")
        result = _run_coupling(ns)

    captured = capsys.readouterr()
    assert result == 0
    assert "requests" in captured.out


def test_run_coupling_json_output(tmp_path, capsys):
    cp = CoupledPackage("flask", "python", ["a", "b"], "3.0.0")
    report = CouplingReport(coupled=[cp])
    with patch("depwatch.cli_coupling.Config") as MockConfig, \
         patch("depwatch.cli_coupling._collect_updates", return_value={}), \
         patch("depwatch.cli_coupling.build_all_digests", return_value=[]), \
         patch("depwatch.cli_coupling.build_coupling_report", return_value=report):
        MockConfig.from_file.return_value = MagicMock()
        ns = _make_namespace(format="json")
        result = _run_coupling(ns)

    captured = capsys.readouterr()
    assert result == 0
    data = json.loads(captured.out)
    assert "coupled_packages" in data
    assert data["total"] == 1
