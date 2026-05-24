"""Diffing module: compare two snapshots or dependency sets and produce a structured diff."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    package: str
    project: str
    language: str
    old_version: Optional[str]
    new_version: Optional[str]
    change: str  # 'added' | 'removed' | 'upgraded' | 'downgraded' | 'unchanged'

    def to_dict(self) -> Dict:
        return {
            "package": self.package,
            "project": self.project,
            "language": self.language,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "change": self.change,
        }


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def by_change(self, change: str) -> List[DiffEntry]:
        return [e for e in self.entries if e.change == change]

    def to_dict(self) -> Dict:
        return {
            "total": len(self.entries),
            "added": len(self.by_change("added")),
            "removed": len(self.by_change("removed")),
            "upgraded": len(self.by_change("upgraded")),
            "downgraded": len(self.by_change("downgraded")),
            "unchanged": len(self.by_change("unchanged")),
            "entries": [e.to_dict() for e in self.entries],
        }

    def summary(self) -> str:
        if self.is_empty():
            return "No differences found."
        parts = []
        for label in ("added", "removed", "upgraded", "downgraded"):
            count = len(self.by_change(label))
            if count:
                parts.append(f"{count} {label}")
        return "Diff: " + ", ".join(parts) if parts else "No significant changes."


def diff_dependency_sets(
    project: str,
    language: str,
    before: Dict[str, str],
    after: Dict[str, str],
) -> DiffResult:
    """Compare two {package: version} dicts and return a DiffResult."""
    entries: List[DiffEntry] = []
    all_packages = set(before) | set(after)

    for pkg in sorted(all_packages):
        old_v = before.get(pkg)
        new_v = after.get(pkg)

        if old_v is None:
            change = "added"
        elif new_v is None:
            change = "removed"
        elif old_v == new_v:
            change = "unchanged"
        else:
            from packaging.version import Version, InvalidVersion
            try:
                change = "upgraded" if Version(new_v.lstrip("v")) > Version(old_v.lstrip("v")) else "downgraded"
            except InvalidVersion:
                change = "upgraded" if new_v > old_v else "downgraded"

        entries.append(DiffEntry(
            package=pkg,
            project=project,
            language=language,
            old_version=old_v,
            new_version=new_v,
            change=change,
        ))

    return DiffResult(entries=entries)
