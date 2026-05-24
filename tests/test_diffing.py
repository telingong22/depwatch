"""Tests for depwatch.diffing."""
from __future__ import annotations

import pytest
from depwatch.diffing import diff_dependency_sets, DiffEntry, DiffResult


BEFORE = {"requests": "2.28.0", "flask": "2.2.0", "old-lib": "1.0.0"}
AFTER  = {"requests": "2.31.0", "flask": "2.2.0", "new-lib": "0.9.0"}


def _run(before=BEFORE, after=AFTER, project="myapp", language="python"):
    return diff_dependency_sets(project, language, before, after)


# ── DiffResult helpers ────────────────────────────────────────────────────────

def test_diff_result_is_empty_when_no_entries():
    r = DiffResult(entries=[])
    assert r.is_empty()


def test_diff_result_not_empty_with_entries():
    r = _run()
    assert not r.is_empty()


def test_diff_result_by_change_upgraded():
    r = _run()
    upgraded = r.by_change("upgraded")
    assert any(e.package == "requests" for e in upgraded)


def test_diff_result_by_change_unchanged():
    r = _run()
    unchanged = r.by_change("unchanged")
    assert any(e.package == "flask" for e in unchanged)


def test_diff_result_by_change_added():
    r = _run()
    added = r.by_change("added")
    assert any(e.package == "new-lib" for e in added)


def test_diff_result_by_change_removed():
    r = _run()
    removed = r.by_change("removed")
    assert any(e.package == "old-lib" for e in removed)


# ── to_dict structure ─────────────────────────────────────────────────────────

def test_to_dict_has_expected_keys():
    d = _run().to_dict()
    for key in ("total", "added", "removed", "upgraded", "downgraded", "unchanged", "entries"):
        assert key in d


def test_to_dict_counts_match():
    r = _run()
    d = r.to_dict()
    assert d["upgraded"] == len(r.by_change("upgraded"))
    assert d["added"] == len(r.by_change("added"))
    assert d["removed"] == len(r.by_change("removed"))


# ── DiffEntry.to_dict ─────────────────────────────────────────────────────────

def test_diff_entry_to_dict_keys():
    entry = DiffEntry(
        package="requests", project="proj", language="python",
        old_version="2.0.0", new_version="3.0.0", change="upgraded"
    )
    d = entry.to_dict()
    assert set(d.keys()) == {"package", "project", "language", "old_version", "new_version", "change"}


# ── downgrade detection ───────────────────────────────────────────────────────

def test_downgrade_detected():
    r = diff_dependency_sets("proj", "python",
                             before={"lib": "3.0.0"},
                             after={"lib": "2.0.0"})
    assert r.by_change("downgraded")[0].package == "lib"


# ── summary text ─────────────────────────────────────────────────────────────

def test_summary_non_empty():
    s = _run().summary()
    assert "Diff:" in s


def test_summary_empty_result():
    r = DiffResult(entries=[])
    assert r.summary() == "No differences found."


# ── identical sets ────────────────────────────────────────────────────────────

def test_identical_sets_all_unchanged():
    deps = {"flask": "2.2.0", "requests": "2.28.0"}
    r = diff_dependency_sets("proj", "python", deps, deps)
    assert all(e.change == "unchanged" for e in r.entries)


def test_empty_before_all_added():
    r = diff_dependency_sets("proj", "python", {}, {"flask": "2.2.0"})
    assert r.by_change("added")[0].package == "flask"


def test_empty_after_all_removed():
    r = diff_dependency_sets("proj", "python", {"flask": "2.2.0"}, {})
    assert r.by_change("removed")[0].package == "flask"
