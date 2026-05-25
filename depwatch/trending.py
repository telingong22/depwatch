"""Detect trending packages — those with the most updates across recent history."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import List

from depwatch.history import HistoryEntry


@dataclass
class TrendEntry:
    package: str
    project: str
    language: str
    update_count: int

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "project": self.project,
            "language": self.language,
            "update_count": self.update_count,
        }

    def __str__(self) -> str:
        return f"{self.project}/{self.package} ({self.language}): {self.update_count} update(s)"


@dataclass
class TrendReport:
    entries: List[TrendEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> dict:
        return {"trending": [e.to_dict() for e in self.entries]}

    def to_text(self) -> str:
        if self.is_empty():
            return "No trending packages."
        lines = ["Trending packages:"]
        for e in self.entries:
            lines.append(f"  {e}")
        return "\n".join(lines)


def build_trend_report(history: List[HistoryEntry], top_n: int = 5) -> TrendReport:
    """Return the top-N packages by number of recorded updates."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    counter: Counter = Counter()
    meta: dict = {}

    for entry in history:
        for update in entry.updates:
            key = (update.project, update.package)
            counter[key] += 1
            meta[key] = {
                "language": getattr(update, "language", "unknown"),
            }

    top = counter.most_common(top_n)
    entries = [
        TrendEntry(
            package=pkg,
            project=proj,
            language=meta.get((proj, pkg), {}).get("language", "unknown"),
            update_count=count,
        )
        for (proj, pkg), count in top
    ]
    return TrendReport(entries=entries)
