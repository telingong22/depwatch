"""Unit tests for depwatch.escalation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.escalation import (
    EscalationRule,
    EscalatedUpdate,
    _overdue_days,
    _is_major,
    evaluate_escalation,
    escalate_all,
)


def _now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_update(
    package: str = "requests",
    current: str = "1.0.0",
    latest: str = "2.0.0",
    first_seen: str | None = None,
) -> UpdateInfo:
    return UpdateInfo(package=package, current=current, latest=latest,
                      language="python", first_seen=first_seen)


def _make_digest(updates: list[UpdateInfo], project: str = "myapp") -> ProjectDigest:
    return ProjectDigest(project=project, updates=updates)


# --- EscalationRule ---

def test_rule_defaults():
    r = EscalationRule()
    assert r.min_overdue_days == 7
    assert r.channel == "email"
    assert r.require_major is False


def test_rule_invalid_days():
    with pytest.raises(ValueError):
        EscalationRule(min_overdue_days=0)


def test_rule_invalid_channel():
    with pytest.raises(ValueError):
        EscalationRule(channel="")


# --- _overdue_days ---

def test_overdue_days_no_first_seen():
    u = _make_update(first_seen=None)
    assert _overdue_days(u, _now()) == 0


def test_overdue_days_ten_days_ago():
    seen = (_now() - timedelta(days=10)).isoformat()
    u = _make_update(first_seen=seen)
    assert _overdue_days(u, _now()) == 10


def test_overdue_days_invalid_string():
    u = _make_update(first_seen="not-a-date")
    assert _overdue_days(u, _now()) == 0


# --- _is_major ---

def test_is_major_true():
    assert _is_major(_make_update(current="1.9.0", latest="2.0.0")) is True


def test_is_major_false_minor():
    assert _is_major(_make_update(current="1.0.0", latest="1.1.0")) is False


def test_is_major_with_v_prefix():
    assert _is_major(_make_update(current="v1.0.0", latest="v2.0.0")) is True


# --- evaluate_escalation ---

def test_evaluate_escalation_overdue():
    seen = (_now() - timedelta(days=10)).isoformat()
    u = _make_update(first_seen=seen)
    rule = EscalationRule(min_overdue_days=7)
    result = evaluate_escalation(_make_digest([u]), rule, _now())
    assert len(result) == 1
    assert result[0].overdue_days == 10


def test_evaluate_escalation_not_overdue():
    seen = (_now() - timedelta(days=3)).isoformat()
    u = _make_update(first_seen=seen)
    rule = EscalationRule(min_overdue_days=7)
    result = evaluate_escalation(_make_digest([u]), rule, _now())
    assert result == []


def test_evaluate_escalation_require_major_filters_minor():
    seen = (_now() - timedelta(days=10)).isoformat()
    u = _make_update(current="1.0.0", latest="1.1.0", first_seen=seen)
    rule = EscalationRule(min_overdue_days=7, require_major=True)
    result = evaluate_escalation(_make_digest([u]), rule, _now())
    assert result == []


def test_evaluate_escalation_require_major_keeps_major():
    seen = (_now() - timedelta(days=10)).isoformat()
    u = _make_update(current="1.0.0", latest="2.0.0", first_seen=seen)
    rule = EscalationRule(min_overdue_days=7, require_major=True)
    result = evaluate_escalation(_make_digest([u]), rule, _now())
    assert len(result) == 1


# --- escalate_all ---

def test_escalate_all_multiple_digests():
    seen = (_now() - timedelta(days=10)).isoformat()
    d1 = _make_digest([_make_update(first_seen=seen)], project="p1")
    d2 = _make_digest([_make_update(first_seen=seen)], project="p2")
    rule = EscalationRule(min_overdue_days=7)
    result = escalate_all([d1, d2], rule, _now())
    assert len(result) == 2
    projects = {e.project for e in result}
    assert projects == {"p1", "p2"}


def test_escalated_update_to_dict():
    seen = (_now() - timedelta(days=10)).isoformat()
    u = _make_update(first_seen=seen)
    rule = EscalationRule(min_overdue_days=7, channel="slack")
    e = EscalatedUpdate(project="myapp", update=u, rule=rule, overdue_days=10)
    d = e.to_dict()
    assert d["project"] == "myapp"
    assert d["channel"] == "slack"
    assert d["overdue_days"] == 10
    assert "package" in d
