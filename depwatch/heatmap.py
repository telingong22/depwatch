"""Heatmap: ranks packages by update frequency across history entries."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from depwatch.history import HistoryEntry


@dataclass
class HeatmapEntry:
    package: str
    language: str
    project: str
    update_count: int

    def to_dict(self) -> Dict:
        return {
            "package": self.package,
            "language": self.language,
            "project": self.project,
            "update_count": self.update_count,
        }

    def __str__(self) -> str:
        return f"{self.package} ({self.language}) [{self.project}]: {self.update_count} updates"


@dataclass
class HeatmapReport:
    entries: List[HeatmapEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def top(self, n: int = 10) -> List[HeatmapEntry]:
        return self.entries[:n]

    def to_dict(self) -> Dict:
        return {"entries": [e.to_dict() for e in self.entries]}


def build_heatmap(history: List[HistoryEntry]) -> HeatmapReport:
    """Count how many times each (project, package, language) tuple appears in history."""
    counter: Counter = Counter()
    meta: Dict[tuple, Dict[str, str]] = {}

    for entry in history:
        for update in entry.updates:
            key = (update.project_name, update.package_name, update.language)
            counter[key] += 1
            if key not in meta:
                meta[key] = {
                    "project": update.project_name,
                    "package": update.package_name,
                    "language": update.language,
                }

    entries = [
        HeatmapEntry(
            package=meta[k]["package"],
            language=meta[k]["language"],
            project=meta[k]["project"],
            update_count=count,
        )
        for k, count in counter.most_common()
    ]
    return HeatmapReport(entries=entries)
