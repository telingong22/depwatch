"""Compare two sets of dependency updates to identify regressions and improvements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from depwatch.checker import UpdateInfo


@dataclass
class ComparisonResult:
    """Outcome of comparing a previous update set against a current one."""
    added: List[UpdateInfo] = field(default_factory=list)      # new updates not in previous
    removed: List[UpdateInfo] = field(default_factory=list)    # updates resolved since previous
    changed: List[UpdateInfo] = field(default_factory=list)    # same package, different latest

    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def to_dict(self) -> Dict:
        return {
            "added": [_update_to_dict(u) for u in self.added],
            "removed": [_update_to_dict(u) for u in self.removed],
            "changed": [_update_to_dict(u) for u in self.changed],
            "summary": {
                "added": len(self.added),
                "removed": len(self.removed),
                "changed": len(self.changed),
            },
        }


def _update_to_dict(u: UpdateInfo) -> Dict:
    return {
        "project": u.project,
        "package": u.package,
        "current": u.current_version,
        "latest": u.latest_version,
        "language": u.language,
    }


def _update_key(u: UpdateInfo) -> str:
    return f"{u.project}::{u.package}"


def compare_updates(
    previous: Sequence[UpdateInfo],
    current: Sequence[UpdateInfo],
) -> ComparisonResult:
    """Return a ComparisonResult describing changes between two update snapshots."""
    prev_map: Dict[str, UpdateInfo] = {_update_key(u): u for u in previous}
    curr_map: Dict[str, UpdateInfo] = {_update_key(u): u for u in current}

    added: List[UpdateInfo] = []
    removed: List[UpdateInfo] = []
    changed: List[UpdateInfo] = []

    for key, curr_u in curr_map.items():
        if key not in prev_map:
            added.append(curr_u)
        elif prev_map[key].latest_version != curr_u.latest_version:
            changed.append(curr_u)

    for key, prev_u in prev_map.items():
        if key not in curr_map:
            removed.append(prev_u)

    return ComparisonResult(added=added, removed=removed, changed=changed)
