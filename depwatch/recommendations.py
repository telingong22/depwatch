"""Recommendation engine: suggest actionable upgrade steps based on digests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from depwatch.digest import ProjectDigest
from depwatch.checker import UpdateInfo


@dataclass
class Recommendation:
    project: str
    package: str
    current_version: str
    latest_version: str
    reason: str
    priority: str  # "high" | "medium" | "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project,
            "package": self.package,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "reason": self.reason,
            "priority": self.priority,
        }

    def __str__(self) -> str:
        return (
            f"[{self.priority.upper()}] {self.project}/{self.package}: "
            f"{self.current_version} -> {self.latest_version} ({self.reason})"
        )


@dataclass
class RecommendationReport:
    items: List[Recommendation] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def by_priority(self, priority: str) -> List[Recommendation]:
        return [r for r in self.items if r.priority == priority]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": len(self.items),
            "high": len(self.by_priority("high")),
            "medium": len(self.by_priority("medium")),
            "low": len(self.by_priority("low")),
            "items": [r.to_dict() for r in self.items],
        }


def _priority_for_update(update: UpdateInfo) -> tuple[str, str]:
    """Return (priority, reason) based on version bump characteristics."""
    current = update.current_version or "0.0.0"
    latest = update.latest_version

    def _major(v: str) -> str:
        return v.lstrip("v").split(".")[0]

    try:
        if _major(current) != _major(latest) and _major(latest) != "0":
            return "high", "major version bump"
    except Exception:
        pass

    if current in ("unknown", "0.0.0", ""):
        return "medium", "unpinned or unknown current version"

    return "low", "minor or patch update available"


def build_recommendations(digests: List[ProjectDigest]) -> RecommendationReport:
    """Build a RecommendationReport from a list of ProjectDigests."""
    items: List[Recommendation] = []
    for digest in digests:
        for update in digest.updates:
            priority, reason = _priority_for_update(update)
            items.append(
                Recommendation(
                    project=digest.project_name,
                    package=update.package_name,
                    current_version=update.current_version or "unknown",
                    latest_version=update.latest_version,
                    reason=reason,
                    priority=priority,
                )
            )
    items.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}[r.priority])
    return RecommendationReport(items=items)
