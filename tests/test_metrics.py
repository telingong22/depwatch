"""Tests for depwatch.metrics."""
from datetime import datetime, timezone

import pytest

from depwatch.metrics import (
    MetricsStore,
    RunMetrics,
    get_store,
    reset_store,
)


def _make_run(**kwargs) -> RunMetrics:
    defaults = dict(
        projects_checked=2,
        packages_checked=10,
        updates_found=3,
        fetch_errors=0,
        notifications_sent=1,
    )
    defaults.update(kwargs)
    return RunMetrics(**defaults)


# ---------------------------------------------------------------------------
# RunMetrics
# ---------------------------------------------------------------------------

def test_run_metrics_to_dict_keys():
    run = _make_run()
    d = run.to_dict()
    assert set(d.keys()) == {
        "started_at",
        "projects_checked",
        "packages_checked",
        "updates_found",
        "fetch_errors",
        "notifications_sent",
    }


def test_run_metrics_to_dict_values():
    run = _make_run(updates_found=5, fetch_errors=2)
    d = run.to_dict()
    assert d["updates_found"] == 5
    assert d["fetch_errors"] == 2


def test_run_metrics_started_at_is_iso():
    run = RunMetrics()
    iso = run.to_dict()["started_at"]
    # Should parse without error
    datetime.fromisoformat(iso)


def test_run_metrics_summary_contains_counts():
    run = _make_run(projects_checked=3, updates_found=7, fetch_errors=1)
    s = run.summary()
    assert "projects=3" in s
    assert "updates=7" in s
    assert "errors=1" in s


# ---------------------------------------------------------------------------
# MetricsStore
# ---------------------------------------------------------------------------

def test_store_empty_initially():
    store = MetricsStore()
    assert store.total_runs() == 0
    assert store.total_updates() == 0
    assert store.total_errors() == 0
    assert store.last() is None


def test_store_record_increments_runs():
    store = MetricsStore()
    store.record(_make_run())
    assert store.total_runs() == 1


def test_store_totals_accumulate():
    store = MetricsStore()
    store.record(_make_run(updates_found=3, fetch_errors=1))
    store.record(_make_run(updates_found=5, fetch_errors=2))
    assert store.total_updates() == 8
    assert store.total_errors() == 3


def test_store_last_returns_most_recent():
    store = MetricsStore()
    r1 = _make_run(updates_found=1)
    r2 = _make_run(updates_found=9)
    store.record(r1)
    store.record(r2)
    assert store.last() is r2


def test_store_to_dict_structure():
    store = MetricsStore()
    store.record(_make_run())
    d = store.to_dict()
    assert d["total_runs"] == 1
    assert isinstance(d["runs"], list)
    assert len(d["runs"]) == 1


# ---------------------------------------------------------------------------
# Module-level store helpers
# ---------------------------------------------------------------------------

def test_reset_store_clears_runs():
    reset_store()
    store = get_store()
    store.record(_make_run())
    assert store.total_runs() == 1
    reset_store()
    assert get_store().total_runs() == 0


def test_get_store_returns_same_instance():
    reset_store()
    assert get_store() is get_store()
