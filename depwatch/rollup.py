"""rollup.py – aggregate per-project digests into a single cross-project rollup summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest


@dataclass
class RollupEntry:
    project: str
    language: str
    total_updates: int
    major: int
    minor: int
    patch: int
    packages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "language": self.language,
            "total_updates": self.total_updates,
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "packages": self.packages,
        }


@dataclass
class Rollup:
    entries: List[RollupEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def total_updates(self) -> int:
        return sum(e.total_updates for e in self.entries)

    def to_dict(self) -> dict:
        return {
            "total_updates": self.total_updates(),
            "projects": [e.to_dict() for e in self.entries],
        }

    def to_text(self) -> str:
        if self.is_empty():
            return "No updates across all projects."
        lines = [f"Rollup: {self.total_updates()} update(s) across {len(self.entries)} project(s)"]
        for e in self.entries:
            lines.append(
                f"  [{e.language}] {e.project}: {e.total_updates} update(s) "
                f"(major={e.major}, minor={e.minor}, patch={e.patch})"
            )
        return "\n".join(lines)


def _bump_counts(updates: List[UpdateInfo]) -> Dict[str, int]:
    from depwatch.filter import _bump_level  # local import to avoid circular deps

    counts: Dict[str, int] = {"major": 0, "minor": 0, "patch": 0}
    for u in updates:
        level = _bump_level(u.current_version, u.latest_version)
        if level in counts:
            counts[level] += 1
        else:
            counts["patch"] += 1
    return counts


def build_rollup(digests: List[ProjectDigest]) -> Rollup:
    """Build a Rollup from a list of ProjectDigest objects."""
    entries: List[RollupEntry] = []
    for digest in digests:
        if digest.is_empty():
            continue
        counts = _bump_counts(digest.updates)
        entry = RollupEntry(
            project=digest.project_name,
            language=digest.language,
            total_updates=len(digest.updates),
            major=counts["major"],
            minor=counts["minor"],
            patch=counts["patch"],
            packages=[u.package for u in digest.updates],
        )
        entries.append(entry)
    return Rollup(entries=entries)
