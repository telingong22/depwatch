"""Velocity tracking: measures how fast each package accumulates updates over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


@dataclass
class VelocityEntry:
    package: str
    project: str
    language: str
    update_count: int
    days_tracked: int
    updates_per_day: float

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "project": self.project,
            "language": self.language,
            "update_count": self.update_count,
            "days_tracked": self.days_tracked,
            "updates_per_day": round(self.updates_per_day, 4),
        }

    def __str__(self) -> str:
        return (
            f"{self.package} ({self.project}): "
            f"{self.update_count} update(s) over {self.days_tracked}d "
            f"= {self.updates_per_day:.4f}/day"
        )


@dataclass
class VelocityReport:
    entries: List[VelocityEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def fastest(self, n: int = 5) -> List[VelocityEntry]:
        return sorted(self.entries, key=lambda e: e.updates_per_day, reverse=True)[:n]

    def to_dict(self) -> dict:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "fastest": [e.to_dict() for e in self.fastest()],
        }


def _days_since(iso_str: Optional[str], now: datetime) -> int:
    if not iso_str:
        return 1
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = now - dt.astimezone(timezone.utc).replace(tzinfo=None)
        return max(1, delta.days)
    except (ValueError, TypeError):
        return 1


def build_velocity(
    digests: List[ProjectDigest],
    history_counts: Optional[Dict[str, int]] = None,
    now: Optional[datetime] = None,
) -> VelocityReport:
    """Build a velocity report from digests.

    history_counts maps ``project:package`` -> total historical update count.
    When absent, each current update contributes 1.
    """
    if now is None:
        now = datetime.utcnow()
    if history_counts is None:
        history_counts = {}

    entries: List[VelocityEntry] = []
    for digest in digests:
        for update in digest.updates:
            key = f"{update.project_name}:{update.package_name}"
            count = history_counts.get(key, 1)
            days = _days_since(getattr(update, "published_at", None), now)
            rate = count / days
            entries.append(
                VelocityEntry(
                    package=update.package_name,
                    project=update.project_name,
                    language=update.language,
                    update_count=count,
                    days_tracked=days,
                    updates_per_day=rate,
                )
            )

    return VelocityReport(entries=entries)
