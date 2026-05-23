"""Tests for depwatch.alerting."""
from __future__ import annotations

import pytest

from depwatch.alerting import AlertThreshold, evaluate_threshold
from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.filter import FilterConfig
from depwatch.fetcher import ReleaseInfo


def _make_update(name: str, current: str, latest: str) -> UpdateInfo:
    return UpdateInfo(
        package=name,
        current_version=current,
        latest_version=latest,
        release=ReleaseInfo(version=latest, published_at="2024-01-01T00:00:00Z"),
    )


def _make_digest(name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project=name, updates=updates)


# --- AlertThreshold validation ---

def test_threshold_invalid_min_updates():
    with pytest.raises(ValueError):
        AlertThreshold(min_updates=0)


def test_threshold_default_is_one():
    t = AlertThreshold()
    assert t.min_updates == 1


# --- evaluate_threshold ---

def test_alert_when_updates_meet_minimum():
    digests = [_make_digest("proj", [_make_update("requests", "2.0.0", "2.1.0")])]
    decision = evaluate_threshold(digests, AlertThreshold(min_updates=1))
    assert decision.should_alert is True


def test_no_alert_when_below_minimum():
    digests = [_make_digest("proj", [_make_update("requests", "2.0.0", "2.1.0")])]
    decision = evaluate_threshold(digests, AlertThreshold(min_updates=3))
    assert decision.should_alert is False
    assert "1 update" in decision.reason


def test_no_alert_empty_digests():
    decision = evaluate_threshold([], AlertThreshold(min_updates=1))
    assert decision.should_alert is False


def test_require_major_blocks_minor_only():
    digests = [_make_digest("proj", [_make_update("flask", "2.1.0", "2.2.0")])]
    decision = evaluate_threshold(digests, AlertThreshold(require_major=True))
    assert decision.should_alert is False
    assert "major" in decision.reason


def test_require_major_passes_with_major_bump():
    digests = [_make_digest("proj", [_make_update("django", "3.2.0", "4.0.0")])]
    decision = evaluate_threshold(digests, AlertThreshold(require_major=True))
    assert decision.should_alert is True


def test_filter_reduces_count_below_threshold():
    fc = FilterConfig(ignored_packages=["requests"])
    digests = [_make_digest("proj", [_make_update("requests", "2.0", "2.1")])]
    decision = evaluate_threshold(digests, AlertThreshold(min_updates=1, filter=fc))
    assert decision.should_alert is False


def test_decision_carries_filtered_digests():
    digests = [
        _make_digest("proj", [
            _make_update("requests", "2.0.0", "2.1.0"),
            _make_update("flask", "1.0.0", "2.0.0"),
        ])
    ]
    decision = evaluate_threshold(digests, AlertThreshold(min_updates=1))
    assert len(decision.digests) == 1
    assert len(decision.digests[0].updates) == 2


def test_reason_includes_count_on_success():
    digests = [_make_digest("p", [_make_update("x", "1.0", "1.1")])]
    decision = evaluate_threshold(digests, AlertThreshold())
    assert "1" in decision.reason
