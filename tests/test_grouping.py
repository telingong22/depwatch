"""Tests for depwatch.grouping."""
from __future__ import annotations

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.grouping import GroupedUpdates, group_digests, group_updates


def _make_update(current: str, latest: str, package: str = "pkg") -> UpdateInfo:
    return UpdateInfo(project="proj", package=package, current_version=current, latest_version=latest)


# ---------------------------------------------------------------------------
# GroupedUpdates helpers
# ---------------------------------------------------------------------------

def test_grouped_updates_is_empty_when_no_updates():
    g = GroupedUpdates()
    assert g.is_empty()


def test_grouped_updates_not_empty_with_major():
    g = GroupedUpdates(major=[_make_update("1.0.0", "2.0.0")])
    assert not g.is_empty()


def test_grouped_updates_summary_empty():
    g = GroupedUpdates()
    assert g.summary() == "no updates"


def test_grouped_updates_summary_counts():
    g = GroupedUpdates(
        major=[_make_update("1.0.0", "2.0.0")],
        minor=[_make_update("1.0.0", "1.1.0"), _make_update("2.0.0", "2.1.0")],
    )
    summary = g.summary()
    assert "1 major" in summary
    assert "2 minor" in summary


def test_grouped_updates_to_dict_keys():
    g = GroupedUpdates(patch=[_make_update("1.0.0", "1.0.1")])
    d = g.to_dict()
    assert set(d.keys()) == {"major", "minor", "patch", "unknown"}


def test_grouped_updates_to_dict_entry_structure():
    u = _make_update("1.0.0", "2.0.0", package="requests")
    g = GroupedUpdates(major=[u])
    entry = g.to_dict()["major"][0]
    assert entry["package"] == "requests"
    assert entry["current"] == "1.0.0"
    assert entry["latest"] == "2.0.0"


# ---------------------------------------------------------------------------
# group_updates
# ---------------------------------------------------------------------------

def test_group_updates_major():
    updates = [_make_update("1.0.0", "2.0.0")]
    g = group_updates(updates)
    assert len(g.major) == 1
    assert g.minor == [] and g.patch == []


def test_group_updates_minor():
    updates = [_make_update("1.0.0", "1.1.0")]
    g = group_updates(updates)
    assert len(g.minor) == 1


def test_group_updates_patch():
    updates = [_make_update("1.0.0", "1.0.1")]
    g = group_updates(updates)
    assert len(g.patch) == 1


def test_group_updates_mixed():
    updates = [
        _make_update("1.0.0", "2.0.0"),
        _make_update("1.0.0", "1.1.0"),
        _make_update("1.0.0", "1.0.1"),
    ]
    g = group_updates(updates)
    assert len(g.major) == 1
    assert len(g.minor) == 1
    assert len(g.patch) == 1


def test_group_updates_empty_input():
    g = group_updates([])
    assert g.is_empty()


# ---------------------------------------------------------------------------
# group_digests
# ---------------------------------------------------------------------------

def test_group_digests_aggregates_across_projects():
    d1 = ProjectDigest(project="a", updates=[_make_update("1.0.0", "2.0.0")])
    d2 = ProjectDigest(project="b", updates=[_make_update("1.0.0", "1.1.0")])
    g = group_digests([d1, d2])
    assert len(g.major) == 1
    assert len(g.minor) == 1


def test_group_digests_empty_digests():
    g = group_digests([])
    assert g.is_empty()
