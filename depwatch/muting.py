"""Muting: temporarily silence alerts for specific packages."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from depwatch.checker import UpdateInfo

_DEFAULT_PATH = Path("depwatch_mutes.json")


@dataclass
class MuteRule:
    project: str        # "*" matches any project
    package: str        # "*" matches any package
    until: Optional[str] = None  # ISO-8601 date; None means indefinite

    def is_active(self) -> bool:
        """Return True if the mute is still in effect."""
        if self.until is None:
            return True
        try:
            expiry = datetime.fromisoformat(self.until).replace(tzinfo=timezone.utc)
        except ValueError:
            return False
        return datetime.now(tz=timezone.utc) < expiry

    def matches(self, update: UpdateInfo) -> bool:
        if not self.is_active():
            return False
        project_match = self.project == "*" or self.project == update.project_name
        package_match = self.package == "*" or self.package.lower() == update.package.lower()
        return project_match and package_match

    def to_dict(self) -> dict:
        return {"project": self.project, "package": self.package, "until": self.until}

    @staticmethod
    def from_dict(data: dict) -> "MuteRule":
        return MuteRule(
            project=data["project"],
            package=data["package"],
            until=data.get("until"),
        )


@dataclass
class MuteStore:
    rules: List[MuteRule] = field(default_factory=list)

    def is_muted(self, update: UpdateInfo) -> bool:
        return any(r.matches(update) for r in self.rules)

    def add(self, rule: MuteRule) -> None:
        self.rules.append(rule)

    def prune_expired(self) -> int:
        """Remove expired rules; returns count removed."""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.is_active()]
        return before - len(self.rules)


def load_mutes(path: Path = _DEFAULT_PATH) -> MuteStore:
    if not path.exists():
        return MuteStore()
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return MuteStore()
    if not isinstance(raw, list):
        return MuteStore()
    rules = [MuteRule.from_dict(r) for r in raw if isinstance(r, dict)]
    return MuteStore(rules=rules)


def save_mutes(store: MuteStore, path: Path = _DEFAULT_PATH) -> None:
    path.write_text(json.dumps([r.to_dict() for r in store.rules], indent=2))


def apply_mutes(updates: List[UpdateInfo], store: MuteStore) -> List[UpdateInfo]:
    """Return only updates that are not muted."""
    return [u for u in updates if not store.is_muted(u)]
