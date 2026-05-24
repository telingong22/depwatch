"""Tests for depwatch.badges."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from depwatch.badges import (
    BadgeInfo,
    _colour_for_digest,
    _encode,
    build_badge,
    build_all_badges,
)
from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


def _make_update(current: str, latest: str) -> UpdateInfo:
    return UpdateInfo(
        project="proj",
        package="pkg",
        current_version=current,
        latest_version=latest,
    )


def _make_digest(updates: list) -> ProjectDigest:
    return ProjectDigest(project="proj", updates=updates)


# ---------------------------------------------------------------------------
# _encode
# ---------------------------------------------------------------------------

def test_encode_replaces_hyphens():
    assert _encode("up-to-date") == "up--to--date"


def test_encode_replaces_spaces():
    assert _encode("2 updates") == "2_updates"


def test_encode_replaces_underscores():
    assert _encode("my_project") == "my__project"


# ---------------------------------------------------------------------------
# _colour_for_digest
# ---------------------------------------------------------------------------

def test_colour_up_to_date_when_empty():
    digest = _make_digest([])
    assert _colour_for_digest(digest) == "brightgreen"


def test_colour_orange_for_minor_update():
    digest = _make_digest([_make_update("1.2.0", "1.3.0")])
    assert _colour_for_digest(digest) == "orange"


def test_colour_red_for_major_update():
    digest = _make_digest([_make_update("1.0.0", "2.0.0")])
    assert _colour_for_digest(digest) == "red"


def test_colour_red_for_major_with_v_prefix():
    digest = _make_digest([_make_update("v1.0.0", "v2.0.0")])
    assert _colour_for_digest(digest) == "red"


# ---------------------------------------------------------------------------
# build_badge
# ---------------------------------------------------------------------------

def test_build_badge_up_to_date():
    badge = build_badge(_make_digest([]))
    assert badge.message == "up to date"
    assert badge.colour == "brightgreen"
    assert badge.label == "depwatch"


def test_build_badge_one_update():
    badge = build_badge(_make_digest([_make_update("1.0", "1.1")]))
    assert badge.message == "1 update"


def test_build_badge_multiple_updates():
    updates = [_make_update("1.0", "1.1"), _make_update("2.0", "2.1")]
    badge = build_badge(_make_digest(updates))
    assert badge.message == "2 updates"


# ---------------------------------------------------------------------------
# BadgeInfo helpers
# ---------------------------------------------------------------------------

def test_to_dict_keys():
    badge = BadgeInfo(project="p", label="depwatch", message="ok", colour="green")
    d = badge.to_dict()
    assert set(d.keys()) == {"project", "label", "message", "colour", "schemaVersion"}


def test_to_shields_url_contains_message():
    badge = BadgeInfo(project="p", label="depwatch", message="up to date", colour="brightgreen")
    url = badge.to_shields_url()
    assert "shields.io" in url
    assert "up_to_date" in url


# ---------------------------------------------------------------------------
# build_all_badges
# ---------------------------------------------------------------------------

def test_build_all_badges_returns_one_per_digest():
    digests = [_make_digest([]), _make_digest([_make_update("1", "2")])]
    badges = build_all_badges(digests)
    assert len(badges) == 2


def test_build_all_badges_empty_list():
    assert build_all_badges([]) == []
