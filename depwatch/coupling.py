"""Coupling analysis: detect packages shared across multiple projects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.digest import ProjectDigest
from depwatch.checker import UpdateInfo


@dataclass
class CoupledPackage:
    package: str
    language: str
    projects: List[str]
    latest_version: str

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "language": self.language,
            "projects": sorted(self.projects),
            "latest_version": self.latest_version,
            "project_count": len(self.projects),
        }

    def __str__(self) -> str:
        projects_str = ", ".join(sorted(self.projects))
        return (
            f"{self.package} ({self.language}) @ {self.latest_version} "
            f"— shared by: {projects_str}"
        )


@dataclass
class CouplingReport:
    coupled: List[CoupledPackage] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.coupled) == 0

    def to_dict(self) -> dict:
        return {
            "coupled_packages": [c.to_dict() for c in self.coupled],
            "total": len(self.coupled),
        }

    def summary(self) -> str:
        if self.is_empty():
            return "No coupled packages found."
        lines = [f"Coupled packages ({len(self.coupled)}):"] + [
            f"  {c}" for c in self.coupled
        ]
        return "\n".join(lines)


def build_coupling_report(digests: List[ProjectDigest]) -> CouplingReport:
    """Find packages that appear in more than one project digest."""
    # key -> (language, latest_version, [project_names])
    seen: Dict[str, dict] = {}

    for digest in digests:
        for update in digest.updates:
            key = f"{update.language}::{update.package}"
            if key not in seen:
                seen[key] = {
                    "language": update.language,
                    "latest": update.latest_version,
                    "projects": [],
                }
            if digest.project_name not in seen[key]["projects"]:
                seen[key]["projects"].append(digest.project_name)

    coupled = [
        CoupledPackage(
            package=key.split("::", 1)[1],
            language=data["language"],
            projects=data["projects"],
            latest_version=data["latest"],
        )
        for key, data in seen.items()
        if len(data["projects"]) > 1
    ]
    coupled.sort(key=lambda c: (-len(c.projects), c.package))
    return CouplingReport(coupled=coupled)
