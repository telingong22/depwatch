"""Dependency update priority scoring.

Assigns a numeric priority score to an UpdateInfo so that digests can be
sorted or filtered by urgency before alerting.

Score components
----------------
- Bump level  : major=40, minor=20, patch=5
- Days stale  : +1 per day since the release (capped at 30)
- Security tag: +50 when the package name appears in *security_packages*
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from depwatch.checker import UpdateInfo
from depwatch.filter import _bump_level  # reuse existing helper

_BUMP_SCORES: dict[str, int] = {
    "major": 40,
    "minor": 20,
    "patch": 5,
    "unknown": 2,
}

_STALE_CAP_DAYS = 30


@dataclass(frozen=True)
class PriorityScore:
    package: str
    project: str
    score: int
    breakdown: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "project": self.project,
            "score": self.score,
            "breakdown": self.breakdown,
        }


def _stale_days(released_at: str | None) -> int:
    """Return days since *released_at* ISO timestamp, capped at _STALE_CAP_DAYS."""
    if not released_at:
        return 0
    try:
        dt = datetime.fromisoformat(released_at.rstrip("Z"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, min(int(delta.days), _STALE_CAP_DAYS))
    except (ValueError, TypeError):
        return 0


def score_update(
    update: UpdateInfo,
    security_packages: Sequence[str] | None = None,
) -> PriorityScore:
    """Compute a *PriorityScore* for a single *UpdateInfo*."""
    bump = _bump_level(update.current_version, update.latest_version)
    bump_score = _BUMP_SCORES.get(bump, _BUMP_SCORES["unknown"])

    released_at = getattr(update.release_info, "published_at", None)
    stale = _stale_days(released_at)

    sec_names = {p.lower() for p in (security_packages or [])}
    security_bonus = 50 if update.package_name.lower() in sec_names else 0

    total = bump_score + stale + security_bonus
    breakdown = {"bump": bump_score, "stale": stale, "security": security_bonus}
    return PriorityScore(
        package=update.package_name,
        project=update.project_name,
        score=total,
        breakdown=breakdown,
    )


def rank_updates(
    updates: Sequence[UpdateInfo],
    security_packages: Sequence[str] | None = None,
) -> list[tuple[UpdateInfo, PriorityScore]]:
    """Return *updates* sorted descending by priority score."""
    scored = [
        (u, score_update(u, security_packages)) for u in updates
    ]
    scored.sort(key=lambda pair: pair[1].score, reverse=True)
    return scored
