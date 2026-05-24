"""Group updates by bump level (major/minor/patch) across all project digests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.filter import _bump_level


@dataclass
class GroupedUpdates:
    """Updates partitioned by semantic bump level."""

    major: List[UpdateInfo] = field(default_factory=list)
    minor: List[UpdateInfo] = field(default_factory=list)
    patch: List[UpdateInfo] = field(default_factory=list)
    unknown: List[UpdateInfo] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.major or self.minor or self.patch or self.unknown)

    def to_dict(self) -> Dict[str, list]:
        return {
            "major": [_update_to_dict(u) for u in self.major],
            "minor": [_update_to_dict(u) for u in self.minor],
            "patch": [_update_to_dict(u) for u in self.patch],
            "unknown": [_update_to_dict(u) for u in self.unknown],
        }

    def summary(self) -> str:
        parts = []
        if self.major:
            parts.append(f"{len(self.major)} major")
        if self.minor:
            parts.append(f"{len(self.minor)} minor")
        if self.patch:
            parts.append(f"{len(self.patch)} patch")
        if self.unknown:
            parts.append(f"{len(self.unknown)} unknown")
        return ", ".join(parts) if parts else "no updates"


def _update_to_dict(u: UpdateInfo) -> dict:
    return {
        "project": u.project,
        "package": u.package,
        "current": u.current_version,
        "latest": u.latest_version,
    }


def group_updates(updates: List[UpdateInfo]) -> GroupedUpdates:
    """Partition a flat list of UpdateInfo objects by bump level."""
    result = GroupedUpdates()
    for u in updates:
        level = _bump_level(u.current_version, u.latest_version)
        if level == "major":
            result.major.append(u)
        elif level == "minor":
            result.minor.append(u)
        elif level == "patch":
            result.patch.append(u)
        else:
            result.unknown.append(u)
    return result


def group_digests(digests: List[ProjectDigest]) -> GroupedUpdates:
    """Collect all updates from multiple ProjectDigest objects and group them."""
    all_updates: List[UpdateInfo] = []
    for digest in digests:
        all_updates.extend(digest.updates)
    return group_updates(all_updates)
