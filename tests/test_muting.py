"""Tests for depwatch.muting."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.checker import UpdateInfo
from depwatch.muting import (
    MuteRule,
    MuteStore,
    apply_mutes,
    load_mutes,
    save_mutes,
)


def _make_update(project="myapp", package="requests", current="2.28.0", latest="2.29.0"):
    return UpdateInfo(
        project_name=project,
        package=package,
        current_version=current,
        latest_version=latest,
        language="python",
    )


def _future(days=10) -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(days=days)).isoformat()


def _past(days=10) -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()


# --- MuteRule ---

def test_mute_rule_active_indefinite():
    rule = MuteRule(project="myapp", package="requests", until=None)
    assert rule.is_active() is True


def test_mute_rule_active_future_expiry():
    rule = MuteRule(project="myapp", package="requests", until=_future())
    assert rule.is_active() is True


def test_mute_rule_inactive_past_expiry():
    rule = MuteRule(project="myapp", package="requests", until=_past())
    assert rule.is_active() is False


def test_mute_rule_matches_exact():
    rule = MuteRule(project="myapp", package="requests")
    assert rule.matches(_make_update()) is True


def test_mute_rule_wildcard_project():
    rule = MuteRule(project="*", package="requests")
    assert rule.matches(_make_update(project="other")) is True


def test_mute_rule_wildcard_package():
    rule = MuteRule(project="myapp", package="*")
    assert rule.matches(_make_update(package="flask")) is True


def test_mute_rule_no_match_different_package():
    rule = MuteRule(project="myapp", package="flask")
    assert rule.matches(_make_update(package="requests")) is False


def test_mute_rule_expired_does_not_match():
    rule = MuteRule(project="myapp", package="requests", until=_past())
    assert rule.matches(_make_update()) is False


def test_mute_rule_round_trip():
    rule = MuteRule(project="myapp", package="requests", until="2099-01-01T00:00:00+00:00")
    assert MuteRule.from_dict(rule.to_dict()) == rule


# --- MuteStore ---

def test_store_is_muted_true():
    store = MuteStore(rules=[MuteRule(project="myapp", package="requests")])
    assert store.is_muted(_make_update()) is True


def test_store_is_muted_false_empty():
    assert MuteStore().is_muted(_make_update()) is False


def test_store_prune_removes_expired():
    rules = [
        MuteRule(project="a", package="x", until=_past()),
        MuteRule(project="b", package="y", until=_future()),
    ]
    store = MuteStore(rules=rules)
    removed = store.prune_expired()
    assert removed == 1
    assert len(store.rules) == 1


# --- persistence ---

def test_load_mutes_missing_file(tmp_path):
    store = load_mutes(tmp_path / "nope.json")
    assert store.rules == []


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "mutes.json"
    store = MuteStore(rules=[MuteRule(project="myapp", package="requests", until=_future())])
    save_mutes(store, path)
    loaded = load_mutes(path)
    assert len(loaded.rules) == 1
    assert loaded.rules[0].package == "requests"


def test_load_mutes_invalid_json(tmp_path):
    path = tmp_path / "mutes.json"
    path.write_text("not json")
    store = load_mutes(path)
    assert store.rules == []


# --- apply_mutes ---

def test_apply_mutes_removes_muted():
    updates = [_make_update(package="requests"), _make_update(package="flask")]
    store = MuteStore(rules=[MuteRule(project="myapp", package="requests")])
    result = apply_mutes(updates, store)
    assert len(result) == 1
    assert result[0].package == "flask"


def test_apply_mutes_empty_store_passes_all():
    updates = [_make_update(), _make_update(package="flask")]
    result = apply_mutes(updates, MuteStore())
    assert len(result) == 2
