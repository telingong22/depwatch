"""Staleness detection: flag packages that have not been updated for a long time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest

_DEFAULT_STALE_DAYS = 180


@dataclass
class StalenessEntry:
    project: str
    package: str
    language: str
    current_version: str
    latest_version: str
    days_since_release: int
    stale: bool

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "days_since_release": self.days_since_release,
            "stale": self.stale,
        }


@dataclass
class StalenessReport:
    entries: List[StalenessEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def stale_only(self) -> List[StalenessEntry]:
        return [e for e in self.entries if e.stale]

    def to_dict(self) -> dict:
        return {
            "total": len(self.entries),
            "stale_count": len(self.stale_only()),
            "entries": [e.to_dict() for e in self.entries],
        }


def _days_since(released_at: Optional[str]) -> int:
    """Return whole days between *released_at* ISO string and now, or 0."""
    if not released_at:
        return 0
    try:
        dt = datetime.fromisoformat(released_at.rstrip("Z"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, delta.days)
    except (ValueError, TypeError):
        return 0


def evaluate_staleness(
    digest: ProjectDigest,
    stale_days: int = _DEFAULT_STALE_DAYS,
) -> StalenessReport:
    """Build a StalenessReport from a ProjectDigest."""
    entries: List[StalenessEntry] = []
    for update in digest.updates:
        days = _days_since(getattr(update.release, "released_at", None))
        entries.append(
            StalenessEntry(
                project=digest.project_name,
                package=update.package,
                language=update.language,
                current_version=update.current_version,
                latest_version=update.latest_version,
                days_since_release=days,
                stale=days >= stale_days,
            )
        )
    return StalenessReport(entries=entries)


def evaluate_all(
    digests: List[ProjectDigest],
    stale_days: int = _DEFAULT_STALE_DAYS,
) -> StalenessReport:
    """Combine staleness reports across all project digests."""
    all_entries: List[StalenessEntry] = []
    for digest in digests:
        all_entries.extend(evaluate_staleness(digest, stale_days).entries)
    return StalenessReport(entries=all_entries)
