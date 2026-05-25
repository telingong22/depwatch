"""Impact analysis: estimate the blast radius of pending updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.filter import _bump_level


@dataclass
class ImpactEntry:
    package: str
    latest: str
    bump: str                  # major / minor / patch / unknown
    affected_projects: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "latest": self.latest,
            "bump": self.bump,
            "affected_projects": sorted(self.affected_projects),
            "project_count": len(self.affected_projects),
        }

    def __str__(self) -> str:
        projects = ", ".join(sorted(self.affected_projects))
        return (
            f"{self.package} {self.latest} ({self.bump}) "
            f"— affects {len(self.affected_projects)} project(s): {projects}"
        )


@dataclass
class ImpactReport:
    entries: List[ImpactEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> dict:
        return {
            "total_packages": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }

    def high_impact(self, min_projects: int = 2) -> List[ImpactEntry]:
        """Return entries that affect at least *min_projects* projects."""
        return [e for e in self.entries if len(e.affected_projects) >= min_projects]


def build_impact_report(digests: Dict[str, ProjectDigest]) -> ImpactReport:
    """Aggregate cross-project impact from a mapping of project digests."""
    # package -> ImpactEntry (keyed by package + latest)
    index: Dict[str, ImpactEntry] = {}

    for project_name, digest in digests.items():
        for update in digest.updates:
            key = f"{update.package}=={update.latest}"
            if key not in index:
                bump = _bump_level(update.current, update.latest)
                index[key] = ImpactEntry(
                    package=update.package,
                    latest=update.latest,
                    bump=bump,
                )
            if project_name not in index[key].affected_projects:
                index[key].affected_projects.append(project_name)

    entries = sorted(
        index.values(),
        key=lambda e: (-len(e.affected_projects), e.package),
    )
    return ImpactReport(entries=entries)
