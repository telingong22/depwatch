"""Integration tests for the escalation pipeline."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.escalation import EscalationRule, escalate_all


def _now() -> datetime:
    return datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)


def _u(
    package: str,
    current: str,
    latest: str,
    days_ago: int | None,
) -> UpdateInfo:
    first_seen = (
        (_now() - timedelta(days=days_ago)).isoformat() if days_ago is not None else None
    )
    return UpdateInfo(
        package=package, current=current, latest=latest,
        language="python", first_seen=first_seen,
    )


def _d(project: str, updates: list[UpdateInfo]) -> ProjectDigest:
    return ProjectDigest(project=project, updates=updates)


def test_only_overdue_updates_escalated():
    updates = [
        _u("old-pkg", "1.0.0", "2.0.0", days_ago=10),
        _u("new-pkg", "1.0.0", "1.1.0", days_ago=2),
    ]
    rule = EscalationRule(min_overdue_days=7)
    result = escalate_all([_d("proj", updates)], rule, _now())
    assert len(result) == 1
    assert result[0].update.package == "old-pkg"


def test_major_only_excludes_minor_even_if_overdue():
    updates = [
        _u("major-pkg", "1.0.0", "2.0.0", days_ago=10),
        _u("minor-pkg", "1.0.0", "1.5.0", days_ago=10),
    ]
    rule = EscalationRule(min_overdue_days=7, require_major=True)
    result = escalate_all([_d("proj", updates)], rule, _now())
    assert len(result) == 1
    assert result[0].update.package == "major-pkg"


def test_no_first_seen_never_escalated():
    updates = [_u("unknown", "1.0.0", "2.0.0", days_ago=None)]
    rule = EscalationRule(min_overdue_days=1)
    result = escalate_all([_d("proj", updates)], rule, _now())
    assert result == []


def test_multiple_projects_aggregated():
    rule = EscalationRule(min_overdue_days=5)
    d1 = _d("alpha", [_u("pkg-a", "1.0", "2.0", days_ago=6)])
    d2 = _d("beta", [_u("pkg-b", "1.0", "2.0", days_ago=6)])
    d3 = _d("gamma", [_u("pkg-c", "1.0", "1.1", days_ago=1)])
    result = escalate_all([d1, d2, d3], rule, _now())
    assert len(result) == 2
    projects = {e.project for e in result}
    assert projects == {"alpha", "beta"}
