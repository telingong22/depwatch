"""Tests for depwatch.approval and depwatch.cli_approval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depwatch.approval import (
    ApprovalRecord,
    filter_unapproved,
    get_status,
    load_approvals,
    save_approvals,
    set_approval,
    _record_key,
)
from depwatch.checker import UpdateInfo
from depwatch.cli_approval import _run_approval, add_approval_parser


def _make_update(project="myproject", package="requests", latest="2.32.0") -> UpdateInfo:
    return UpdateInfo(project=project, package=package, current="2.31.0", latest=latest, language="python")


# --- ApprovalRecord ---

def test_record_key_format():
    assert _record_key("proj", "pkg", "1.0") == "proj::pkg::1.0"


def test_approval_record_round_trip():
    rec = ApprovalRecord(project="p", package="q", version="1.0", status="approved", note="ok")
    restored = ApprovalRecord.from_dict(rec.to_dict())
    assert restored.project == "p"
    assert restored.status == "approved"
    assert restored.note == "ok"


def test_approval_record_to_dict_keys():
    rec = ApprovalRecord(project="p", package="q", version="1.0", status="pending")
    keys = set(rec.to_dict())
    assert keys == {"project", "package", "version", "status", "author", "note", "timestamp"}


# --- load / save ---

def test_load_approvals_missing_file(tmp_path):
    result = load_approvals(tmp_path / "nope.json")
    assert result == {}


def test_load_approvals_invalid_json(tmp_path):
    f = tmp_path / "a.json"
    f.write_text("not json")
    assert load_approvals(f) == {}


def test_load_approvals_wrong_type(tmp_path):
    f = tmp_path / "a.json"
    f.write_text(json.dumps({"x": 1}))
    assert load_approvals(f) == {}


def test_save_and_load_round_trip(tmp_path):
    f = tmp_path / "approvals.json"
    rec = ApprovalRecord(project="proj", package="pkg", version="1.0", status="approved")
    save_approvals({"proj::pkg::1.0": rec}, f)
    loaded = load_approvals(f)
    assert "proj::pkg::1.0" in loaded
    assert loaded["proj::pkg::1.0"].status == "approved"


# --- set_approval / get_status ---

def test_set_approval_creates_record(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    rec = set_approval(u, status="approved", path=f)
    assert rec.status == "approved"
    assert f.exists()


def test_set_approval_invalid_status(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    with pytest.raises(ValueError):
        set_approval(u, status="maybe", path=f)


def test_get_status_returns_none_when_missing(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    assert get_status(u, path=f) is None


def test_get_status_returns_record(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    set_approval(u, status="rejected", path=f)
    rec = get_status(u, path=f)
    assert rec is not None
    assert rec.status == "rejected"


# --- filter_unapproved ---

def test_filter_unapproved_keeps_pending(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    result = filter_unapproved([u], path=f)
    assert u in result


def test_filter_unapproved_removes_approved(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    set_approval(u, status="approved", path=f)
    result = filter_unapproved([u], path=f)
    assert u not in result


def test_filter_unapproved_keeps_rejected(tmp_path):
    f = tmp_path / "approvals.json"
    u = _make_update()
    set_approval(u, status="rejected", path=f)
    result = filter_unapproved([u], path=f)
    assert u in result


# --- CLI ---

def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = dict(
        cmd="list", project="", package="", version="",
        author="depwatch", note="", file="depwatch_approvals.json", format="text",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_approval_parser_registers_subcommand():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_approval_parser(sub)
    args = p.parse_args(["approval", "list"])
    assert hasattr(args, "func")


def test_run_approval_list_empty(tmp_path, capsys):
    f = tmp_path / "approvals.json"
    ns = _make_namespace(cmd="list", file=str(f))
    rc = _run_approval(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No approval record" in out


def test_run_approval_approve_then_list(tmp_path, capsys):
    f = tmp_path / "approvals.json"
    ns = _make_namespace(cmd="approve", project="proj", package="requests", version="2.32.0", file=str(f))
    rc = _run_approval(ns)
    assert rc == 0
    ns2 = _make_namespace(cmd="list", file=str(f), format="json")
    _run_approval(ns2)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert any(d["status"] == "approved" for d in data)


def test_run_approval_missing_fields_returns_error(tmp_path, capsys):
    f = tmp_path / "approvals.json"
    ns = _make_namespace(cmd="approve", project="", package="", version="", file=str(f))
    rc = _run_approval(ns)
    assert rc == 1
