"""Cluster updates by ecosystem, bump level, and recency."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.filter import _bump_level


@dataclass
class Cluster:
    key: str          # e.g. "python/major", "go/minor"
    language: str
    bump: str         # major | minor | patch | unknown
    updates: List[UpdateInfo] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.updates) == 0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "language": self.language,
            "bump": self.bump,
            "count": len(self.updates),
            "packages": [
                {"project": u.project_name, "package": u.package_name,
                 "current": u.current_version, "latest": u.latest_version}
                for u in self.updates
            ],
        }

    def __str__(self) -> str:
        return f"[{self.key}] {len(self.updates)} update(s)"


@dataclass
class ClusterReport:
    clusters: List[Cluster] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.clusters) == 0

    def to_dict(self) -> dict:
        return {"clusters": [c.to_dict() for c in self.clusters]}

    def summary(self) -> str:
        if self.is_empty():
            return "No clusters."
        lines = [str(c) for c in self.clusters]
        return "\n".join(lines)


def build_clusters(digests: Dict[str, ProjectDigest]) -> ClusterReport:
    """Group all updates across projects into language+bump clusters."""
    bucket: Dict[str, Cluster] = {}

    for digest in digests.values():
        for update in digest.updates:
            lang = update.language or "unknown"
            bump = _bump_level(update.current_version, update.latest_version)
            key = f"{lang}/{bump}"
            if key not in bucket:
                bucket[key] = Cluster(key=key, language=lang, bump=bump)
            bucket[key].updates.append(update)

    clusters = sorted(bucket.values(), key=lambda c: (c.language, c.bump))
    return ClusterReport(clusters=clusters)
