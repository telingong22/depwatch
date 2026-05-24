"""Tests for depwatch.tagging."""
from __future__ import annotations

import argparse
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from depwatch.checker import UpdateInfo
from depwatch.tagging import (
    TagRule,
    TaggedUpdate,
    _apply_rules,
    rules_from_config,
    tag_all,
    tag_update,
)


def _make_update(package: str = "requests", language: str = "python") -> UpdateInfo:
    return UpdateInfo(
        project="myapp",
        package=package,
        current="1.0.0",
        latest="2.0.0",
        language=language,
    )


# ---------------------------------------------------------------------------
# TagRule.matches
# ---------------------------------------------------------------------------

def test_tag_rule_exact_match():
    rule = TagRule(pattern="requests", tag="http")
    assert rule.matches("requests")


def test_tag_rule_wildcard_match():
    rule = TagRule(pattern="boto*", tag="aws")
    assert rule.matches("boto3")
    assert rule.matches("botocore")


def test_tag_rule_no_match():
    rule = TagRule(pattern="boto*", tag="aws")
    assert not rule.matches("requests")


def test_tag_rule_case_insensitive():
    rule = TagRule(pattern="Requests", tag="http")
    assert rule.matches("REQUESTS")


# ---------------------------------------------------------------------------
# _apply_rules
# ---------------------------------------------------------------------------

def test_apply_rules_returns_all_matching_tags():
    rules = [
        TagRule(pattern="requests", tag="http"),
        TagRule(pattern="req*", tag="networking"),
    ]
    tags = _apply_rules("requests", rules)
    assert "http" in tags
    assert "networking" in tags


def test_apply_rules_deduplicates_tags():
    rules = [
        TagRule(pattern="req*", tag="http"),
        TagRule(pattern="requests", tag="http"),
    ]
    tags = _apply_rules("requests", rules)
    assert tags.count("http") == 1


def test_apply_rules_empty_rules_returns_empty():
    assert _apply_rules("requests", []) == []


# ---------------------------------------------------------------------------
# tag_update / tag_all
# ---------------------------------------------------------------------------

def test_tag_update_attaches_tags():
    rules = [TagRule(pattern="requests", tag="http")]
    result = tag_update(_make_update("requests"), rules)
    assert isinstance(result, TaggedUpdate)
    assert result.tags == ["http"]


def test_tag_update_no_matching_rule_gives_empty_tags():
    result = tag_update(_make_update("flask"), [TagRule(pattern="requests", tag="http")])
    assert result.tags == []


def test_tag_all_processes_every_update():
    updates = [_make_update("requests"), _make_update("flask")]
    rules = [TagRule(pattern="requests", tag="http")]
    results = tag_all(updates, rules)
    assert len(results) == 2
    assert results[0].tags == ["http"]
    assert results[1].tags == []


# ---------------------------------------------------------------------------
# rules_from_config
# ---------------------------------------------------------------------------

def test_rules_from_config_valid():
    raw = [{"pattern": "boto*", "tag": "aws"}, {"pattern": "requests", "tag": "http"}]
    rules = rules_from_config(raw)
    assert len(rules) == 2
    assert rules[0].tag == "aws"


def test_rules_from_config_skips_invalid_entries():
    raw = [{"pattern": "boto*", "tag": "aws"}, {"bad": "entry"}, None]
    rules = rules_from_config(raw)  # type: ignore[arg-type]
    assert len(rules) == 1


def test_rules_from_config_none_returns_empty():
    assert rules_from_config(None) == []


# ---------------------------------------------------------------------------
# TaggedUpdate.to_dict
# ---------------------------------------------------------------------------

def test_tagged_update_to_dict_keys():
    result = tag_update(_make_update("requests"), [TagRule("requests", "http")])
    d = result.to_dict()
    assert set(d.keys()) == {"project", "package", "current", "latest", "language", "tags"}


def test_tagged_update_to_dict_values():
    result = tag_update(_make_update("requests"), [TagRule("requests", "http")])
    d = result.to_dict()
    assert d["package"] == "requests"
    assert d["tags"] == ["http"]
