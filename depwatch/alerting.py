"""Threshold-based alerting: suppress notifications unless update count meets criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.digest import ProjectDigest
from depwatch.filter import FilterConfig, apply_filter


@dataclass
class AlertThreshold:
    """Criteria that must be met before an alert is dispatched."""
    min_updates: int = 1           # minimum total updates across all projects
    require_major: bool = False    # only alert when at least one major bump exists
    filter: FilterConfig = field(default_factory=FilterConfig)

    def __post_init__(self) -> None:
        if self.min_updates < 1:
            raise ValueError("min_updates must be >= 1")


@dataclass
class AlertDecision:
    should_alert: bool
    reason: str
    digests: List[ProjectDigest]


def _has_major(digests: List[ProjectDigest]) -> bool:
    for digest in digests:
        for upd in digest.updates:
            current = upd.current_version.lstrip("v")
            latest = upd.latest_version.lstrip("v")
            try:
                cur_major = int(current.split(".")[0])
                lat_major = int(latest.split(".")[0])
                if lat_major > cur_major:
                    return True
            except (ValueError, IndexError):
                continue
    return False


def evaluate_threshold(
    digests: List[ProjectDigest],
    threshold: AlertThreshold,
) -> AlertDecision:
    """Apply threshold rules and return an AlertDecision."""
    filtered: List[ProjectDigest] = []
    for digest in digests:
        kept = apply_filter(digest.updates, threshold.filter)
        if kept:
            from depwatch.digest import ProjectDigest as PD
            filtered.append(PD(project=digest.project, updates=kept))

    total = sum(len(d.updates) for d in filtered)

    if total < threshold.min_updates:
        return AlertDecision(
            should_alert=False,
            reason=f"only {total} update(s), need {threshold.min_updates}",
            digests=filtered,
        )

    if threshold.require_major and not _has_major(filtered):
        return AlertDecision(
            should_alert=False,
            reason="no major-version bumps found",
            digests=filtered,
        )

    return AlertDecision(
        should_alert=True,
        reason=f"{total} update(s) passed all thresholds",
        digests=filtered,
    )
