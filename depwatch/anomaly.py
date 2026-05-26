"""Anomaly detection: flag packages with unusually high release velocity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from depwatch.digest import ProjectDigest
from depwatch.checker import UpdateInfo


@dataclass
class AnomalyEntry:
    project: str
    package: str
    language: str
    update_count: int  # number of releases seen in current cycle
    threshold: int

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "package": self.package,
            "language": self.language,
            "update_count": self.update_count,
            "threshold": self.threshold,
        }

    def __str__(self) -> str:
        return (
            f"{self.package} ({self.language}) in '{self.project}': "
            f"{self.update_count} updates exceeds threshold {self.threshold}"
        )


@dataclass
class AnomalyReport:
    entries: List[AnomalyEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> Dict:
        return {"anomalies": [e.to_dict() for e in self.entries]}


def _count_per_package(updates: List[UpdateInfo]) -> Dict[str, int]:
    """Return a mapping of package name -> number of UpdateInfo entries."""
    counts: Dict[str, int] = {}
    for u in updates:
        counts[u.package] = counts.get(u.package, 0) + 1
    return counts


def detect_anomalies(
    digests: List[ProjectDigest],
    threshold: int = 3,
) -> AnomalyReport:
    """Flag any package that appears more than *threshold* times across updates.

    A package appearing multiple times usually means rapid successive releases
    within a single polling cycle, which may warrant investigation.
    """
    if threshold < 1:
        raise ValueError("threshold must be >= 1")

    entries: List[AnomalyEntry] = []
    for digest in digests:
        counts = _count_per_package(digest.updates)
        for pkg, count in counts.items():
            if count > threshold:
                lang = digest.updates[0].language if digest.updates else "unknown"
                entries.append(
                    AnomalyEntry(
                        project=digest.project,
                        package=pkg,
                        language=lang,
                        update_count=count,
                        threshold=threshold,
                    )
                )
    return AnomalyReport(entries=entries)
