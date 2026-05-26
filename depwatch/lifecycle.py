"""Lifecycle tracking for dependency updates.

Tracks the lifecycle stage of each dependency update: new, active, resolved, or ignored.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo

STAGES = ("new", "active", "resolved", "ignored")


@dataclass
class LifecycleEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    stage: str
    created_at: str
    updated_at: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "stage": self.stage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "note": self.note,
        }

    @staticmethod
    def from_dict(d: dict) -> "LifecycleEntry":
        return LifecycleEntry(
            project=d["project"],
            package=d["package"],
            current_version=d["current_version"],
            latest_version=d["latest_version"],
            stage=d["stage"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            note=d.get("note", ""),
        )


def _entry_key(project: str, package: str, latest_version: str) -> str:
    return f"{project}::{package}::{latest_version}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_lifecycle(path: str) -> Dict[str, LifecycleEntry]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, dict):
            return {}
        return {k: LifecycleEntry.from_dict(v) for k, v in raw.items()}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_lifecycle(path: str, store: Dict[str, LifecycleEntry]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({k: v.to_dict() for k, v in store.items()}, fh, indent=2)


def upsert_entry(
    store: Dict[str, LifecycleEntry],
    update: UpdateInfo,
    stage: str = "new",
    note: str = "",
) -> LifecycleEntry:
    if stage not in STAGES:
        raise ValueError(f"Invalid stage '{stage}'; must be one of {STAGES}")
    key = _entry_key(update.project_name, update.package, update.latest_version)
    now = _now_iso()
    if key in store:
        entry = store[key]
        entry.stage = stage
        entry.updated_at = now
        if note:
            entry.note = note
    else:
        entry = LifecycleEntry(
            project=update.project_name,
            package=update.package,
            current_version=update.current_version,
            latest_version=update.latest_version,
            stage=stage,
            created_at=now,
            updated_at=now,
            note=note,
        )
        store[key] = entry
    return entry


def entries_by_stage(store: Dict[str, LifecycleEntry], stage: str) -> List[LifecycleEntry]:
    return [e for e in store.values() if e.stage == stage]
