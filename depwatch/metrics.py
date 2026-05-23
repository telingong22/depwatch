"""Simple in-memory metrics collector for tracking depwatch run statistics."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class RunMetrics:
    """Metrics captured during a single depwatch cycle."""

    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    projects_checked: int = 0
    packages_checked: int = 0
    updates_found: int = 0
    fetch_errors: int = 0
    notifications_sent: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "started_at": self.started_at.isoformat(),
            "projects_checked": self.projects_checked,
            "packages_checked": self.packages_checked,
            "updates_found": self.updates_found,
            "fetch_errors": self.fetch_errors,
            "notifications_sent": self.notifications_sent,
        }

    def summary(self) -> str:
        return (
            f"projects={self.projects_checked} "
            f"packages={self.packages_checked} "
            f"updates={self.updates_found} "
            f"errors={self.fetch_errors} "
            f"notifications={self.notifications_sent}"
        )


@dataclass
class MetricsStore:
    """Accumulates RunMetrics across multiple cycles."""

    _runs: List[RunMetrics] = field(default_factory=list)

    def record(self, run: RunMetrics) -> None:
        """Append a completed run's metrics."""
        self._runs.append(run)

    def total_runs(self) -> int:
        return len(self._runs)

    def total_updates(self) -> int:
        return sum(r.updates_found for r in self._runs)

    def total_errors(self) -> int:
        return sum(r.fetch_errors for r in self._runs)

    def last(self) -> RunMetrics | None:
        return self._runs[-1] if self._runs else None

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_runs": self.total_runs(),
            "total_updates": self.total_updates(),
            "total_errors": self.total_errors(),
            "runs": [r.to_dict() for r in self._runs],
        }


# Module-level default store used by the daemon.
_default_store: MetricsStore = MetricsStore()


def get_store() -> MetricsStore:
    """Return the module-level MetricsStore."""
    return _default_store


def reset_store() -> None:
    """Reset the module-level store (useful in tests)."""
    global _default_store
    _default_store = MetricsStore()
