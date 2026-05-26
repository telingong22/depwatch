"""Maturity scoring for dependency updates.

Assigns a maturity level to each update based on how long the latest
version has been available and how many major versions the package has
had, giving teams a signal about release stability.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_days(released_at: Optional[str]) -> int:
    dt = _parse_iso(released_at)
    if dt is None:
        return 0
    now = datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def _maturity_label(age_days: int, is_major: bool) -> str:
    """Return a maturity label based on age and bump type."""
    if is_major and age_days < 14:
        return "new-major"
    if age_days < 7:
        return "fresh"
    if age_days < 30:
        return "recent"
    if age_days < 90:
        return "stable"
    return "mature"


@dataclass
class MaturityScore:
    project: str
    package: str
    latest_version: str
    age_days: int
    label: str
    is_major: bool

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "latest_version": self.latest_version,
            "age_days": self.age_days,
            "label": self.label,
            "is_major": self.is_major,
        }

    def __str__(self) -> str:
        return (
            f"{self.package} {self.latest_version} "
            f"[{self.label}, {self.age_days}d old]"
        )


@dataclass
class MaturityReport:
    scores: List[MaturityScore]

    def is_empty(self) -> bool:
        return len(self.scores) == 0

    def by_label(self, label: str) -> List[MaturityScore]:
        return [s for s in self.scores if s.label == label]

    def to_dict(self) -> dict:
        return {"scores": [s.to_dict() for s in self.scores]}


def _is_major(update: UpdateInfo) -> bool:
    try:
        cur = update.current_version.lstrip("v")
        lat = update.latest_version.lstrip("v")
        cur_major = int(cur.split(".")[0])
        lat_major = int(lat.split(".")[0])
        return lat_major > cur_major
    except (ValueError, IndexError):
        return False


def score_update(project: str, update: UpdateInfo) -> MaturityScore:
    age = _age_days(getattr(update.release_info, "published_at", None))
    major = _is_major(update)
    label = _maturity_label(age, major)
    return MaturityScore(
        project=project,
        package=update.package_name,
        latest_version=update.latest_version,
        age_days=age,
        label=label,
        is_major=major,
    )


def build_maturity_report(digests: List[ProjectDigest]) -> MaturityReport:
    scores: List[MaturityScore] = []
    for digest in digests:
        for update in digest.updates:
            scores.append(score_update(digest.project_name, update))
    scores.sort(key=lambda s: s.age_days)
    return MaturityReport(scores=scores)
