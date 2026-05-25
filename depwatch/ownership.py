"""Ownership mapping: assign owners/teams to packages across projects."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from typing import Dict, List, Optional
import json
import os

from depwatch.checker import UpdateInfo


@dataclass
class OwnerRule:
    """A rule that maps a package glob to an owner string."""
    package: str          # glob pattern, e.g. "django*" or "*"
    owner: str            # team or individual, e.g. "backend-team"
    project: str = "*"   # optional project glob filter

    def matches(self, update: UpdateInfo) -> bool:
        return (
            fnmatchcase(update.project_name.lower(), self.project.lower())
            and fnmatchcase(update.package.lower(), self.package.lower())
        )

    def to_dict(self) -> dict:
        return {"package": self.package, "owner": self.owner, "project": self.project}

    @classmethod
    def from_dict(cls, d: dict) -> "OwnerRule":
        return cls(
            package=d["package"],
            owner=d["owner"],
            project=d.get("project", "*"),
        )


@dataclass
class OwnedUpdate:
    """An update annotated with its resolved owner (or None)."""
    update: UpdateInfo
    owner: Optional[str]

    def to_dict(self) -> dict:
        return {
            "project": self.update.project_name,
            "package": self.update.package,
            "current": self.update.current_version,
            "latest": self.update.latest_version,
            "owner": self.owner,
        }


def resolve_owner(update: UpdateInfo, rules: List[OwnerRule]) -> Optional[str]:
    """Return the first matching owner for *update*, or None."""
    for rule in rules:
        if rule.matches(update):
            return rule.owner
    return None


def annotate_updates(
    updates: List[UpdateInfo],
    rules: List[OwnerRule],
) -> List[OwnedUpdate]:
    """Annotate every update with its resolved owner."""
    return [OwnedUpdate(update=u, owner=resolve_owner(u, rules)) for u in updates]


def load_ownership(path: str) -> List[OwnerRule]:
    """Load ownership rules from a JSON file. Returns [] if file is missing."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, list):
        raise ValueError("ownership file must contain a JSON array")
    return [OwnerRule.from_dict(item) for item in raw]


def save_ownership(rules: List[OwnerRule], path: str) -> None:
    """Persist ownership rules to *path* as JSON."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([r.to_dict() for r in rules], fh, indent=2)
