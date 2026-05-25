"""Tests for depwatch.ownership."""
from __future__ import annotations

import json
import os
import pytest

from depwatch.checker import UpdateInfo
from depwatch.ownership import (
    OwnerRule,
    OwnedUpdate,
    resolve_owner,
    annotate_updates,
    load_ownership,
    save_ownership,
)


def _make_update(package: str = "requests", project: str = "my-service") -> UpdateInfo:
    return UpdateInfo(
        project_name=project,
        package=package,
        current_version="1.0.0",
        latest_version="2.0.0",
        language="python",
    )


# ---------------------------------------------------------------------------
# OwnerRule.matches
# ---------------------------------------------------------------------------

def test_rule_exact_match():
    rule = OwnerRule(package="requests", owner="backend")
    assert rule.matches(_make_update("requests"))


def test_rule_glob_match():
    rule = OwnerRule(package="django*", owner="web-team")
    assert rule.matches(_make_update("django-rest-framework"))


def test_rule_no_match_different_package():
    rule = OwnerRule(package="flask", owner="web-team")
    assert not rule.matches(_make_update("requests"))


def test_rule_project_filter_matches():
    rule = OwnerRule(package="*", owner="sre", project="infra-*")
    assert rule.matches(_make_update(project="infra-core"))


def test_rule_project_filter_excludes():
    rule = OwnerRule(package="*", owner="sre", project="infra-*")
    assert not rule.matches(_make_update(project="my-service"))


# ---------------------------------------------------------------------------
# OwnerRule round-trip
# ---------------------------------------------------------------------------

def test_owner_rule_round_trip():
    rule = OwnerRule(package="boto3*", owner="cloud-team", project="aws-*")
    restored = OwnerRule.from_dict(rule.to_dict())
    assert restored.package == rule.package
    assert restored.owner == rule.owner
    assert restored.project == rule.project


def test_owner_rule_default_project_is_wildcard():
    rule = OwnerRule.from_dict({"package": "requests", "owner": "backend"})
    assert rule.project == "*"


# ---------------------------------------------------------------------------
# resolve_owner / annotate_updates
# ---------------------------------------------------------------------------

def test_resolve_owner_first_rule_wins():
    rules = [
        OwnerRule(package="requests", owner="first"),
        OwnerRule(package="requests", owner="second"),
    ]
    assert resolve_owner(_make_update("requests"), rules) == "first"


def test_resolve_owner_no_match_returns_none():
    rules = [OwnerRule(package="flask", owner="web")]
    assert resolve_owner(_make_update("requests"), rules) is None


def test_annotate_updates_assigns_owners():
    updates = [_make_update("requests"), _make_update("flask")]
    rules = [OwnerRule(package="requests", owner="backend")]
    result = annotate_updates(updates, rules)
    assert len(result) == 2
    owners = {r.update.package: r.owner for r in result}
    assert owners["requests"] == "backend"
    assert owners["flask"] is None


def test_owned_update_to_dict_keys():
    u = _make_update()
    owned = OwnedUpdate(update=u, owner="platform")
    d = owned.to_dict()
    assert set(d.keys()) == {"project", "package", "current", "latest", "owner"}


# ---------------------------------------------------------------------------
# load_ownership / save_ownership
# ---------------------------------------------------------------------------

def test_load_ownership_missing_file(tmp_path):
    rules = load_ownership(str(tmp_path / "missing.json"))
    assert rules == []


def test_save_and_load_round_trip(tmp_path):
    rules = [
        OwnerRule(package="requests", owner="backend"),
        OwnerRule(package="django*", owner="web", project="web-*"),
    ]
    path = str(tmp_path / "ownership.json")
    save_ownership(rules, path)
    loaded = load_ownership(path)
    assert len(loaded) == 2
    assert loaded[0].owner == "backend"
    assert loaded[1].project == "web-*"


def test_load_ownership_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    with pytest.raises(Exception):
        load_ownership(str(p))


def test_load_ownership_wrong_type_raises(tmp_path):
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps({"package": "requests", "owner": "x"}))
    with pytest.raises(ValueError):
        load_ownership(str(p))


def test_save_ownership_creates_file(tmp_path):
    path = str(tmp_path / "sub" / "ownership.json")
    save_ownership([OwnerRule(package="*", owner="all")], path)
    assert os.path.exists(path)
