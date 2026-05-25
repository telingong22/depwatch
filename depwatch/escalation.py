"""Escalation rules: promote an alert to a higher-severity channel when
certain conditions are met (e.g. a package has been overdue for N days)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


@dataclass
class EscalationRule:
    """A single escalation rule."""
    min_overdue_days: int = 7          # days since first_seen before escalating
    require_major: bool = False        # only escalate on major bumps
    channel: str = "email"            # target channel label (informational)

    def __post_init__(self) -> None:
        if self.min_overdue_days < 1:
            raise ValueError("min_overdue_days must be >= 1")
        if not self.channel:
            raise ValueError("channel must not be empty")


@dataclass
class EscalatedUpdate:
    """An update that has been flagged for escalation."""
    project: str
    update: UpdateInfo
    rule: EscalationRule
    overdue_days: int

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.update.package,
            "current": self.update.current,
            "latest": self.update.latest,
            "overdue_days": self.overdue_days,
            "channel": self.rule.channel,
        }


def _overdue_days(update: UpdateInfo, now: Optional[datetime] = None) -> int:
    """Return how many days ago *first_seen* was, or 0 if unknown."""
    if not update.first_seen:
        return 0
    try:
        seen = datetime.fromisoformat(update.first_seen)
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        delta = (now or datetime.now(timezone.utc)) - seen
        return max(0, delta.days)
    except (ValueError, TypeError):
        return 0


def _is_major(update: UpdateInfo) -> bool:
    try:
        cur = tuple(int(x) for x in update.current.lstrip("v").split(".")[:1])
        lat = tuple(int(x) for x in update.latest.lstrip("v").split(".")[:1])
        return lat > cur
    except (ValueError, AttributeError):
        return False


def evaluate_escalation(
    digest: ProjectDigest,
    rule: EscalationRule,
    now: Optional[datetime] = None,
) -> List[EscalatedUpdate]:
    """Return updates in *digest* that satisfy *rule*."""
    results: List[EscalatedUpdate] = []
    for update in digest.updates:
        if rule.require_major and not _is_major(update):
            continue
        days = _overdue_days(update, now)
        if days >= rule.min_overdue_days:
            results.append(EscalatedUpdate(
                project=digest.project,
                update=update,
                rule=rule,
                overdue_days=days,
            ))
    return results


def escalate_all(
    digests: List[ProjectDigest],
    rule: EscalationRule,
    now: Optional[datetime] = None,
) -> List[EscalatedUpdate]:
    """Run *evaluate_escalation* across all digests."""
    out: List[EscalatedUpdate] = []
    for digest in digests:
        out.extend(evaluate_escalation(digest, rule, now))
    return out
