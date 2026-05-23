"""Tests for depwatch.state."""

import json
from pathlib import Path

import pytest

from depwatch.state import (
    get_last_seen,
    load_state,
    save_state,
    set_last_seen,
)


# ---------------------------------------------------------------------------
# load_state
# ---------------------------------------------------------------------------

def test_load_state_missing_file(tmp_path):
    result = load_state(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_state_valid(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"proj/requests": "2.31.0"}), encoding="utf-8")
    result = load_state(state_file)
    assert result == {"proj/requests": "2.31.0"}


def test_load_state_invalid_json(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("not json", encoding="utf-8")
    result = load_state(state_file)
    assert result == {}


def test_load_state_wrong_type(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    result = load_state(state_file)
    assert result == {}


# ---------------------------------------------------------------------------
# save_state
# ---------------------------------------------------------------------------

def test_save_state_creates_file(tmp_path):
    state_file = tmp_path / "state.json"
    save_state({"proj/flask": "3.0.0"}, state_file)
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data == {"proj/flask": "3.0.0"}


def test_save_state_overwrites(tmp_path):
    state_file = tmp_path / "state.json"
    save_state({"proj/a": "1.0"}, state_file)
    save_state({"proj/a": "2.0"}, state_file)
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["proj/a"] == "2.0"


def test_save_state_no_tmp_file_left(tmp_path):
    state_file = tmp_path / "state.json"
    save_state({}, state_file)
    assert not (tmp_path / "state.tmp").exists()


# ---------------------------------------------------------------------------
# get_last_seen / set_last_seen
# ---------------------------------------------------------------------------

def test_get_last_seen_missing():
    assert get_last_seen({}, "myproject", "requests") is None


def test_set_and_get_last_seen():
    state = {}
    set_last_seen(state, "myproject", "requests", "2.28.0")
    assert get_last_seen(state, "myproject", "requests") == "2.28.0"


def test_set_last_seen_updates_existing():
    state = {"myproject/requests": "2.27.0"}
    set_last_seen(state, "myproject", "requests", "2.28.0")
    assert get_last_seen(state, "myproject", "requests") == "2.28.0"


def test_keys_are_namespaced():
    state = {}
    set_last_seen(state, "proj_a", "lib", "1.0")
    set_last_seen(state, "proj_b", "lib", "2.0")
    assert get_last_seen(state, "proj_a", "lib") == "1.0"
    assert get_last_seen(state, "proj_b", "lib") == "2.0"
