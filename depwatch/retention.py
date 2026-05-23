"""Retention policy: prune history entries older than a configured age."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from depwatch.history import HistoryEntry, load_history, save_history


@dataclass
class RetentionPolicy:
    """Controls how long history entries are kept."""
    max_days: int = 90

    def __post_init__(self) -> None:
        if self.max_days < 1:
            raise ValueError("max_days must be at least 1")

    @property
    def cutoff(self) -> datetime:
        return datetime.now(tz=timezone.utc) - timedelta(days=self.max_days)


def apply_retention(entries: List[HistoryEntry], policy: RetentionPolicy) -> List[HistoryEntry]:
    """Return only entries whose timestamp is within the retention window."""
    cutoff = policy.cutoff
    return [e for e in entries if e.timestamp >= cutoff]


def prune_history(path: str, policy: RetentionPolicy) -> int:
    """Load history at *path*, drop stale entries, persist, return pruned count."""
    entries = load_history(path)
    kept = apply_retention(entries, policy)
    pruned = len(entries) - len(kept)
    if pruned > 0:
        save_history(path, kept)
    return pruned
