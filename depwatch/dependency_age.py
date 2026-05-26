"""Compute age-related statistics for current dependency versions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _age_days(published: Optional[str]) -> int:
    dt = _parse_iso(published)
    if dt is None:
        return 0
    now = datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    return max(0, delta.days)


@dataclass
class AgeEntry:
    project: str
    package: str
    language: str
    current_version: str
    latest_version: str
    published_at: Optional[str]
    age_days: int

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "published_at": self.published_at,
            "age_days": self.age_days,
        }

    def __str__(self) -> str:
        return (
            f"{self.project}/{self.package} "
            f"({self.language}) latest={self.latest_version} "
            f"age={self.age_days}d"
        )


@dataclass
class AgeReport:
    entries: List[AgeEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def oldest_first(self) -> List[AgeEntry]:
        return sorted(self.entries, key=lambda e: e.age_days, reverse=True)

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.oldest_first()]}


def _entry_from_update(update: UpdateInfo) -> AgeEntry:
    age = _age_days(update.release.published_at)
    return AgeEntry(
        project=update.project,
        package=update.package,
        language=update.language,
        current_version=update.current_version,
        latest_version=update.release.version,
        published_at=update.release.published_at,
        age_days=age,
    )


def build_age_report(digests: List[ProjectDigest]) -> AgeReport:
    entries: List[AgeEntry] = []
    for digest in digests:
        for update in digest.updates:
            entries.append(_entry_from_update(update))
    return AgeReport(entries=entries)
