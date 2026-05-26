"""Forecast future update frequency based on historical release cadence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from depwatch.history import HistoryEntry


@dataclass
class ForecastEntry:
    project: str
    package: str
    language: str
    avg_days_between_releases: float
    last_released_at: Optional[str]
    next_expected_at: Optional[str]

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "avg_days_between_releases": round(self.avg_days_between_releases, 2),
            "last_released_at": self.last_released_at,
            "next_expected_at": self.next_expected_at,
        }

    def __str__(self) -> str:
        cadence = f"{self.avg_days_between_releases:.1f}d"
        nxt = self.next_expected_at or "unknown"
        return f"{self.project}/{self.package} ({self.language}): every ~{cadence}, next ~{nxt[:10]}"


@dataclass
class ForecastReport:
    entries: List[ForecastEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> dict:
        return {"forecasts": [e.to_dict() for e in self.entries]}


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _forecast_entry(project: str, package: str, language: str,
                    timestamps: List[datetime]) -> ForecastEntry:
    timestamps = sorted(timestamps)
    last_dt = timestamps[-1] if timestamps else None
    last_iso = last_dt.isoformat() if last_dt else None

    if len(timestamps) < 2:
        return ForecastEntry(
            project=project,
            package=package,
            language=language,
            avg_days_between_releases=0.0,
            last_released_at=last_iso,
            next_expected_at=None,
        )

    gaps = [
        (timestamps[i] - timestamps[i - 1]).total_seconds() / 86400
        for i in range(1, len(timestamps))
    ]
    avg_days = sum(gaps) / len(gaps)
    next_dt = last_dt + timedelta(days=avg_days) if last_dt else None
    next_iso = next_dt.isoformat() if next_dt else None

    return ForecastEntry(
        project=project,
        package=package,
        language=language,
        avg_days_between_releases=avg_days,
        last_released_at=last_iso,
        next_expected_at=next_iso,
    )


def build_forecast(history: List[HistoryEntry]) -> ForecastReport:
    """Derive per-package release cadence forecasts from recorded history."""
    grouped: dict[tuple, list] = {}
    for entry in history:
        key = (entry.project, entry.package, entry.language)
        dt = _parse_iso(entry.detected_at)
        if dt is not None:
            grouped.setdefault(key, []).append(dt)

    entries = [
        _forecast_entry(project, package, language, timestamps)
        for (project, package, language), timestamps in sorted(grouped.items())
    ]
    return ForecastReport(entries=entries)
