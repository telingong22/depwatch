"""Deduplication helpers — prevent the same update from being reported twice
within a single digest cycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from depwatch.checker import UpdateInfo


@dataclass
class DeduplicatedResult:
    """Holds unique updates after deduplication."""

    updates: List[UpdateInfo] = field(default_factory=list)
    dropped: List[UpdateInfo] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.updates) == 0

    def dropped_count(self) -> int:
        return len(self.dropped)


def _update_key(update: UpdateInfo) -> str:
    """Return a string key that uniquely identifies a package update.

    Two UpdateInfo objects with the same project, package name and latest
    version are considered duplicates regardless of the recorded current
    version.
    """
    return f"{update.project_name}::{update.package_name}::{update.latest_version}"


def dedup_updates(updates: Iterable[UpdateInfo]) -> DeduplicatedResult:
    """Remove duplicate UpdateInfo entries, keeping the first occurrence.

    Args:
        updates: Iterable of UpdateInfo objects, possibly containing
                 duplicates produced by multiple fetch/check passes.

    Returns:
        DeduplicatedResult with unique updates and the dropped duplicates.
    """
    seen: set[str] = set()
    unique: List[UpdateInfo] = []
    dropped: List[UpdateInfo] = []

    for update in updates:
        key = _update_key(update)
        if key in seen:
            dropped.append(update)
        else:
            seen.add(key)
            unique.append(update)

    return DeduplicatedResult(updates=unique, dropped=dropped)
