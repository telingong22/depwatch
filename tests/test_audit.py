"""Tests for depwatch.audit and depwatch.cli_audit."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from depwatch.audit import (
    AuditEntry,
    append_audit,
    load_audit,
    record_action,
)
from depwatch.cli_audit import _run_audit


# ---------------------------------------------------------------------------
# AuditEntry unit tests
# ---------------------------------------------------------------------------

def test_audit_entry_to_dict_keys():
    e = AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        action="email_sent",
        project="myapp",
        package="requests",
        current_version="2.28.0",
        latest_version="2.31.0",
        detail="digest",
    )
    keys = set(e.to_dict())
    assert keys == {"timestamp", "action", "project", "package",
                    "current_version", "latest_version", "detail"}


def test_audit_entry_round_trip():
    e = AuditEntry(
        timestamp="2024-06-01T12:00:00+00:00",
        action="suppressed",
        project="svc",
        package="flask",
        current_version="3.0.0",
        latest_version="3.0.1",
    )
    assert AuditEntry.from_dict(e.to_dict()) == e


def test_audit_entry_detail_defaults_empty():
    e = AuditEntry.from_dict({
        "timestamp": "t",
        "action": "a",
        "project": "p",
        "package": "pkg",
        "current_version": "1.0",
        "latest_version": "2.0",
    })
    assert e.detail == ""


# ---------------------------------------------------------------------------
# load_audit / append_audit
# ---------------------------------------------------------------------------

def test_load_audit_missing_file(tmp_path):
    assert load_audit(tmp_path / "nope.json") == []


def test_load_audit_invalid_json(tmp_path):
    p = tmp_path / "audit.json"
    p.write_text("not json")
    assert load_audit(p) == []


def test_load_audit_wrong_type(tmp_path):
    p = tmp_path / "audit.json"
    p.write_text(json.dumps({"bad": "structure"}))
    assert load_audit(p) == []


def test_append_and_load_round_trip(tmp_path):
    p = tmp_path / "audit.json"
    e = AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        action="webhook_sent",
        project="proj",
        package="boto3",
        current_version="1.26",
        latest_version="1.34",
    )
    append_audit(e, p)
    loaded = load_audit(p)
    assert len(loaded) == 1
    assert loaded[0] == e


def test_record_action_writes_entry(tmp_path):
    p = tmp_path / "audit.json"
    entry = record_action("email_sent", "app", "django", "4.1", "4.2", path=p)
    assert entry.action == "email_sent"
    loaded = load_audit(p)
    assert loaded[0].package == "django"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_namespace(**kwargs) -> SimpleNamespace:
    defaults = dict(audit_file="audit.json", action=None, project=None, fmt="text")
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_run_audit_missing_file(tmp_path, capsys):
    ns = _make_namespace(audit_file=str(tmp_path / "nope.json"))
    rc = _run_audit(ns)
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_run_audit_text_output(tmp_path, capsys):
    p = tmp_path / "audit.json"
    record_action("email_sent", "proj", "httpx", "0.23", "0.27", path=p)
    ns = _make_namespace(audit_file=str(p))
    rc = _run_audit(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "email_sent" in out
    assert "httpx" in out


def test_run_audit_json_output(tmp_path, capsys):
    p = tmp_path / "audit.json"
    record_action("suppressed", "proj", "click", "8.0", "8.1", path=p)
    ns = _make_namespace(audit_file=str(p), fmt="json")
    rc = _run_audit(ns)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["package"] == "click"


def test_run_audit_filter_by_action(tmp_path, capsys):
    p = tmp_path / "audit.json"
    record_action("email_sent", "proj", "a", "1", "2", path=p)
    record_action("suppressed", "proj", "b", "1", "2", path=p)
    ns = _make_namespace(audit_file=str(p), action="suppressed")
    _run_audit(ns)
    out = capsys.readouterr().out
    assert "suppressed" in out
    assert "email_sent" not in out


def test_run_audit_empty_after_filter(tmp_path, capsys):
    p = tmp_path / "audit.json"
    record_action("email_sent", "proj", "a", "1", "2", path=p)
    ns = _make_namespace(audit_file=str(p), action="webhook_sent")
    rc = _run_audit(ns)
    assert rc == 0
    assert "No audit" in capsys.readouterr().out
