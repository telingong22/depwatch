"""Unit tests for depwatch.cli_provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depwatch.cli_provenance import add_provenance_parser, _run_provenance
from depwatch.provenance import ProvenanceEntry, save_provenance


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "provenance_file": ".depwatch/provenance.json",
        "format": "text",
        "project": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_provenance_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_provenance_parser(sub)
    args = parser.parse_args(["provenance"])
    assert hasattr(args, "func")


def test_run_provenance_missing_file(tmp_path):
    ns = _make_namespace(provenance_file=str(tmp_path / "missing.json"))
    rc = _run_provenance(ns)
    assert rc == 1


def test_run_provenance_empty_store(tmp_path, capsys):
    f = tmp_path / "prov.json"
    save_provenance(f, {})
    ns = _make_namespace(provenance_file=str(f))
    rc = _run_provenance(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No provenance" in out


def test_run_provenance_text_output(tmp_path, capsys):
    f = tmp_path / "prov.json"
    e = ProvenanceEntry("myapp", "requests", "python",
                        "2024-01-01T00:00:00+00:00", "2.0.0", "pypi")
    save_provenance(f, {"myapp::requests": e})
    ns = _make_namespace(provenance_file=str(f), format="text")
    rc = _run_provenance(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "requests" in out
    assert "pypi" in out


def test_run_provenance_json_output(tmp_path, capsys):
    f = tmp_path / "prov.json"
    e = ProvenanceEntry("myapp", "flask", "python",
                        "2024-02-01T00:00:00+00:00", "3.0.0", "pypi")
    save_provenance(f, {"myapp::flask": e})
    ns = _make_namespace(provenance_file=str(f), format="json")
    rc = _run_provenance(ns)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["package"] == "flask"


def test_run_provenance_project_filter(tmp_path, capsys):
    f = tmp_path / "prov.json"
    e1 = ProvenanceEntry("alpha", "requests", "python",
                         "2024-01-01T00:00:00+00:00", "2.0.0", "pypi")
    e2 = ProvenanceEntry("beta", "flask", "python",
                         "2024-01-02T00:00:00+00:00", "3.0.0", "pypi")
    save_provenance(f, {"alpha::requests": e1, "beta::flask": e2})
    ns = _make_namespace(provenance_file=str(f), format="text", project="alpha")
    rc = _run_provenance(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "requests" in out
    assert "flask" not in out
