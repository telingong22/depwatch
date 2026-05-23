"""Tests for depwatch.throttle."""

from __future__ import annotations

import json
import os
import time

import pytest

from depwatch.throttle import (
    ThrottlePolicy,
    _load_store,
    _save_store,
    filter_throttled,
    is_throttled,
    record_alert,
)


# ---------------------------------------------------------------------------
# ThrottlePolicy
# ---------------------------------------------------------------------------

def test_policy_default_cooldown():
    p = ThrottlePolicy()
    assert p.cooldown_hours == 24
    assert p.cooldown_seconds == 24 * 3600.0


def test_policy_custom_cooldown():
    p = ThrottlePolicy(cooldown_hours=6)
    assert p.cooldown_seconds == 6 * 3600.0


def test_policy_invalid_cooldown():
    with pytest.raises(ValueError):
        ThrottlePolicy(cooldown_hours=0)


# ---------------------------------------------------------------------------
# _load_store / _save_store
# ---------------------------------------------------------------------------

def test_load_store_missing_file(tmp_path):
    result = _load_store(str(tmp_path / "missing.json"))
    assert result == {}


def test_load_store_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    assert _load_store(str(p)) == {}


def test_load_store_wrong_type(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("[1,2,3]", encoding="utf-8")
    assert _load_store(str(p)) == {}


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "store.json")
    store = {"requests": 1700000000.0, "flask": 1700001000.0}
    _save_store(path, store)
    loaded = _load_store(path)
    assert loaded == store


# ---------------------------------------------------------------------------
# is_throttled
# ---------------------------------------------------------------------------

def test_is_throttled_no_prior_record(tmp_path):
    policy = ThrottlePolicy(cooldown_hours=1)
    assert is_throttled("requests", policy, str(tmp_path / "t.json")) is False


def test_is_throttled_recent_record(tmp_path):
    path = str(tmp_path / "t.json")
    policy = ThrottlePolicy(cooldown_hours=1)
    store = {"requests": time.time() - 60}  # 1 minute ago
    _save_store(path, store)
    assert is_throttled("requests", policy, path) is True


def test_is_throttled_expired_record(tmp_path):
    path = str(tmp_path / "t.json")
    policy = ThrottlePolicy(cooldown_hours=1)
    store = {"requests": time.time() - 7200}  # 2 hours ago
    _save_store(path, store)
    assert is_throttled("requests", policy, path) is False


# ---------------------------------------------------------------------------
# record_alert
# ---------------------------------------------------------------------------

def test_record_alert_creates_file(tmp_path):
    path = str(tmp_path / "t.json")
    record_alert("flask", path)
    assert os.path.exists(path)
    store = _load_store(path)
    assert "flask" in store
    assert abs(store["flask"] - time.time()) < 5


def test_record_alert_updates_existing(tmp_path):
    path = str(tmp_path / "t.json")
    _save_store(path, {"flask": 1000.0})
    record_alert("flask", path)
    store = _load_store(path)
    assert store["flask"] > 1000.0


# ---------------------------------------------------------------------------
# filter_throttled
# ---------------------------------------------------------------------------

def test_filter_throttled_removes_recent(tmp_path):
    path = str(tmp_path / "t.json")
    policy = ThrottlePolicy(cooldown_hours=1)
    _save_store(path, {"requests": time.time() - 30})
    result = filter_throttled(["requests", "flask"], policy, path)
    assert result == ["flask"]


def test_filter_throttled_passes_all_when_empty(tmp_path):
    path = str(tmp_path / "t.json")
    policy = ThrottlePolicy(cooldown_hours=1)
    packages = ["requests", "flask", "django"]
    result = filter_throttled(packages, policy, path)
    assert result == packages
