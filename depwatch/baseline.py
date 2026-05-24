"""Baseline management: capture and compare dependency versions over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class BaselineEntry:
    package: str
    version: str
    project: str
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "version": self.version,
            "project": self.project,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineEntry":
        return cls(
            package=data["package"],
            version=data["version"],
            project=data["project"],
            recorded_at=data.get("recorded_at", ""),
        )


def load_baseline(path: str) -> List[BaselineEntry]:
    """Load baseline entries from a JSON file. Returns empty list if missing."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, list):
            return []
        return [BaselineEntry.from_dict(item) for item in raw if isinstance(item, dict)]
    except (json.JSONDecodeError, KeyError):
        return []


def save_baseline(path: str, entries: List[BaselineEntry]) -> None:
    """Persist baseline entries to a JSON file."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([e.to_dict() for e in entries], fh, indent=2)


def diff_baseline(
    old: List[BaselineEntry], new: List[BaselineEntry]
) -> Dict[str, Dict[str, Optional[str]]]:
    """Return packages whose version changed between old and new baselines.

    Returns a dict: {"project/package": {"old": "...", "new": "..."}}.
    """
    old_map = {(e.project, e.package): e.version for e in old}
    new_map = {(e.project, e.package): e.version for e in new}
    changed: Dict[str, Dict[str, Optional[str]]] = {}
    all_keys = set(old_map) | set(new_map)
    for key in all_keys:
        ov = old_map.get(key)
        nv = new_map.get(key)
        if ov != nv:
            changed[f"{key[0]}/{key[1]}"] = {"old": ov, "new": nv}
    return changed
