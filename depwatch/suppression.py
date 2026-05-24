"""Suppression list: skip specific packages from alerting."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from depwatch.checker import UpdateInfo

_DEFAULT_PATH = Path(".depwatch_suppress.json")


@dataclass
class SuppressionList:
    """A set of (project, package) pairs that should be silently skipped."""

    entries: List[dict] = field(default_factory=list)

    def is_suppressed(self, update: UpdateInfo) -> bool:
        """Return True if *update* matches any suppression entry."""
        for entry in self.entries:
            proj_match = entry.get("project") in (None, "", update.project)
            pkg_match = entry.get("package") in (None, "", update.package)
            if proj_match and pkg_match:
                return True
        return False

    def to_dict(self) -> dict:
        return {"suppressed": self.entries}


def load_suppression(path: Optional[Path] = None) -> SuppressionList:
    """Load a suppression list from *path* (defaults to .depwatch_suppress.json).

    Returns an empty SuppressionList when the file is missing or invalid.
    """
    target = path or _DEFAULT_PATH
    try:
        raw = target.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return SuppressionList()
        entries = data.get("suppressed", [])
        if not isinstance(entries, list):
            return SuppressionList()
        return SuppressionList(entries=entries)
    except (FileNotFoundError, json.JSONDecodeError):
        return SuppressionList()


def save_suppression(sl: SuppressionList, path: Optional[Path] = None) -> None:
    """Persist *sl* to *path* as JSON."""
    target = path or _DEFAULT_PATH
    target.write_text(json.dumps(sl.to_dict(), indent=2), encoding="utf-8")


def apply_suppression(
    updates: List[UpdateInfo],
    sl: SuppressionList,
) -> List[UpdateInfo]:
    """Return only those updates that are *not* suppressed."""
    return [u for u in updates if not sl.is_suppressed(u)]
