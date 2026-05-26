"""Unit tests for depwatch.provenance."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.checker import UpdateInfo
from depwatch.provenance import (
    ProvenanceEntry,
    _entry_key,
    _source_for,
    load_provenance,
    record_provenance,
    save_provenance,
)


def _make_update(project="myapp", package="requests", language="python",
                 current="1.0.0", latest="2.0.0") -> UpdateInfo:
    return UpdateInfo(project=project, package=package, language=language,
                      current=current, latest=latest)


def test_entry_key_lowercases_package():
    assert _entry_key("proj", "Requests") == "proj::requests"


def test_source_for_python():
    assert _source_for("python") == "pypi"


def test_source_for_go():
    assert _source_for("go") == "goproxy"


def test_provenance_entry_to_dict_keys():
    e = ProvenanceEntry("p", "pkg", "python", "2024-01-01T00:00:00+00:00", "1.0", "pypi")
    d = e.to_dict()
    assert set(d.keys()) == {"project", "package", "language", "first_seen", "latest_version", "source"}


def test_provenance_entry_round_trip():
    e = ProvenanceEntry("p", "pkg", "go", "2024-06-01T00:00:00+00:00", "v1.2.3", "goproxy")
    assert ProvenanceEntry.from_dict(e.to_dict()) == e


def test_load_provenance_missing_file(tmp_path):
    result = load_provenance(tmp_path / "missing.json")
    assert result == {}


def test_load_provenance_invalid_json(tmp_path):
    f = tmp_path / "prov.json"
    f.write_text("not json")
    assert load_provenance(f) == {}


def test_load_provenance_wrong_type(tmp_path):
    f = tmp_path / "prov.json"
    f.write_text(json.dumps([1, 2, 3]))
    assert load_provenance(f) == {}


def test_save_and_load_round_trip(tmp_path):
    f = tmp_path / "prov.json"
    e = ProvenanceEntry("proj", "flask", "python", "2024-01-01T00:00:00+00:00", "3.0.0", "pypi")
    store = {"proj::flask": e}
    save_provenance(f, store)
    loaded = load_provenance(f)
    assert "proj::flask" in loaded
    assert loaded["proj::flask"].package == "flask"


def test_record_provenance_adds_new_entry():
    u = _make_update()
    store = record_provenance([u], {}, now="2024-03-01T00:00:00+00:00")
    key = "myapp::requests"
    assert key in store
    assert store[key].first_seen == "2024-03-01T00:00:00+00:00"
    assert store[key].source == "pypi"


def test_record_provenance_does_not_overwrite_existing():
    u = _make_update()
    existing = ProvenanceEntry("myapp", "requests", "python",
                               "2023-01-01T00:00:00+00:00", "1.0.0", "pypi")
    store = {"myapp::requests": existing}
    record_provenance([u], store, now="2024-01-01T00:00:00+00:00")
    assert store["myapp::requests"].first_seen == "2023-01-01T00:00:00+00:00"


def test_record_provenance_go_uses_goproxy():
    u = _make_update(language="go", package="github.com/gin-gonic/gin")
    store = record_provenance([u], {})
    key = "myapp::github.com/gin-gonic/gin"
    assert store[key].source == "goproxy"


def test_save_provenance_creates_parent_dirs(tmp_path):
    f = tmp_path / "sub" / "dir" / "prov.json"
    save_provenance(f, {})
    assert f.exists()
    assert json.loads(f.read_text()) == {}
