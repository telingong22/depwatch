"""Tests for depwatch.rollup."""
from __future__ import annotations

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.rollup import Rollup, RollupEntry, build_rollup, _bump_counts


def _make_update(pkg: str, current: str, latest: str, lang: str = "python") -> UpdateInfo:
    return UpdateInfo(
        project="proj",
        package=pkg,
        current_version=current,
        latest_version=latest,
        language=lang,
    )


def _make_digest(
    name: str = "myproject",
    lang: str = "python",
    updates: list | None = None,
) -> ProjectDigest:
    return ProjectDigest(
        project_name=name,
        language=lang,
        updates=updates or [],
    )


# ---------------------------------------------------------------------------
# RollupEntry
# ---------------------------------------------------------------------------

def test_rollup_entry_to_dict_keys():
    entry = RollupEntry(
        project="p", language="python", total_updates=2,
        major=1, minor=1, patch=0, packages=["requests", "flask"]
    )
    d = entry.to_dict()
    assert set(d.keys()) == {"project", "language", "total_updates", "major", "minor", "patch", "packages"}


def test_rollup_entry_to_dict_values():
    entry = RollupEntry(
        project="svc", language="go", total_updates=3,
        major=0, minor=2, patch=1, packages=["gin", "zap", "pgx"]
    )
    d = entry.to_dict()
    assert d["project"] == "svc"
    assert d["language"] == "go"
    assert d["total_updates"] == 3
    assert d["packages"] == ["gin", "zap", "pgx"]


# ---------------------------------------------------------------------------
# Rollup
# ---------------------------------------------------------------------------

def test_rollup_is_empty_when_no_entries():
    r = Rollup(entries=[])
    assert r.is_empty()


def test_rollup_not_empty_with_entries():
    entry = RollupEntry("p", "python", 1, 0, 1, 0, ["flask"])
    r = Rollup(entries=[entry])
    assert not r.is_empty()


def test_rollup_total_updates_sums_entries():
    entries = [
        RollupEntry("a", "python", 3, 1, 1, 1, []),
        RollupEntry("b", "go", 2, 0, 2, 0, []),
    ]
    r = Rollup(entries=entries)
    assert r.total_updates() == 5


def test_rollup_to_dict_structure():
    entry = RollupEntry("p", "python", 1, 1, 0, 0, ["django"])
    r = Rollup(entries=[entry])
    d = r.to_dict()
    assert "total_updates" in d
    assert "projects" in d
    assert len(d["projects"]) == 1


def test_rollup_to_text_empty():
    r = Rollup(entries=[])
    assert "No updates" in r.to_text()


def test_rollup_to_text_non_empty():
    entry = RollupEntry("api", "python", 2, 1, 1, 0, ["requests", "flask"])
    r = Rollup(entries=[entry])
    text = r.to_text()
    assert "api" in text
    assert "2 update" in text


# ---------------------------------------------------------------------------
# build_rollup
# ---------------------------------------------------------------------------

def test_build_rollup_skips_empty_digests():
    digests = [_make_digest("empty", updates=[])]
    rollup = build_rollup(digests)
    assert rollup.is_empty()


def test_build_rollup_counts_updates():
    updates = [
        _make_update("requests", "2.28.0", "2.29.0"),
        _make_update("flask", "2.0.0", "3.0.0"),
    ]
    digest = _make_digest("web", updates=updates)
    rollup = build_rollup([digest])
    assert not rollup.is_empty()
    assert rollup.total_updates() == 2
    assert rollup.entries[0].project == "web"


def test_build_rollup_multiple_projects():
    d1 = _make_digest("svc-a", updates=[_make_update("pkg", "1.0.0", "2.0.0")])
    d2 = _make_digest("svc-b", lang="go", updates=[_make_update("gin", "1.8.0", "1.9.0", "go")])
    rollup = build_rollup([d1, d2])
    assert len(rollup.entries) == 2
    assert rollup.total_updates() == 2


def test_build_rollup_packages_list():
    updates = [_make_update("requests", "2.0", "3.0"), _make_update("flask", "1.0", "2.0")]
    digest = _make_digest("web", updates=updates)
    rollup = build_rollup([digest])
    assert set(rollup.entries[0].packages) == {"requests", "flask"}
