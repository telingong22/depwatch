"""Integration tests: alerting + filter + digest pipeline."""
from __future__ import annotations

from depwatch.alerting import AlertThreshold, evaluate_threshold
from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.fetcher import ReleaseInfo
from depwatch.filter import FilterConfig


def _u(pkg: str, cur: str, lat: str) -> UpdateInfo:
    return UpdateInfo(
        package=pkg,
        current_version=cur,
        latest_version=lat,
        release=ReleaseInfo(version=lat, published_at="2024-06-01T00:00:00Z"),
    )


def _d(name: str, *updates: UpdateInfo) -> ProjectDigest:
    return ProjectDigest(project=name, updates=list(updates))


def test_full_pipeline_passes_all():
    digests = [
        _d("backend", _u("django", "4.1", "4.2"), _u("celery", "5.2", "5.3")),
        _d("frontend", _u("whitenoise", "6.0", "6.1")),
    ]
    decision = evaluate_threshold(digests, AlertThreshold(min_updates=2))
    assert decision.should_alert is True
    total = sum(len(d.updates) for d in decision.digests)
    assert total == 3


def test_filter_removes_ignored_drops_below_threshold():
    fc = FilterConfig(ignored_packages=["celery", "whitenoise"])
    digests = [
        _d("backend", _u("django", "4.1", "4.2"), _u("celery", "5.2", "5.3")),
        _d("frontend", _u("whitenoise", "6.0", "6.1")),
    ]
    decision = evaluate_threshold(
        digests, AlertThreshold(min_updates=2, filter=fc)
    )
    assert decision.should_alert is False


def test_major_bump_triggers_require_major():
    digests = [
        _d("svc", _u("pydantic", "1.10.0", "2.0.0")),
    ]
    decision = evaluate_threshold(digests, AlertThreshold(require_major=True))
    assert decision.should_alert is True


def test_only_minor_suppressed_by_require_major():
    digests = [
        _d("svc", _u("httpx", "0.23.0", "0.24.0"), _u("rich", "13.0", "13.1")),
    ]
    decision = evaluate_threshold(
        digests, AlertThreshold(min_updates=1, require_major=True)
    )
    assert decision.should_alert is False
    assert "major" in decision.reason
