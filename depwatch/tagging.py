"""Tag updates with custom user-defined labels based on package name patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from depwatch.checker import UpdateInfo


@dataclass
class TagRule:
    """A single rule: if pattern matches package name, apply tag."""
    pattern: str
    tag: str

    def matches(self, package: str) -> bool:
        return fnmatch(package.lower(), self.pattern.lower())


@dataclass
class TaggedUpdate:
    update: UpdateInfo
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.update.project,
            "package": self.update.package,
            "current": self.update.current,
            "latest": self.update.latest,
            "language": self.update.language,
            "tags": self.tags,
        }


def _apply_rules(package: str, rules: List[TagRule]) -> List[str]:
    """Return all tags whose rule pattern matches *package*."""
    seen: set = set()
    tags: List[str] = []
    for rule in rules:
        if rule.matches(package) and rule.tag not in seen:
            tags.append(rule.tag)
            seen.add(rule.tag)
    return tags


def tag_update(update: UpdateInfo, rules: List[TagRule]) -> TaggedUpdate:
    """Tag a single update according to *rules*."""
    tags = _apply_rules(update.package, rules)
    return TaggedUpdate(update=update, tags=tags)


def tag_all(
    updates: List[UpdateInfo],
    rules: List[TagRule],
) -> List[TaggedUpdate]:
    """Tag every update in *updates* and return the results."""
    return [tag_update(u, rules) for u in updates]


def rules_from_config(raw: Optional[List[dict]]) -> List[TagRule]:
    """Build a list of :class:`TagRule` objects from a list of dicts.

    Each dict must contain ``pattern`` and ``tag`` keys.
    Invalid entries are silently skipped.
    """
    if not raw:
        return []
    result: List[TagRule] = []
    for item in raw:
        try:
            result.append(TagRule(pattern=item["pattern"], tag=item["tag"]))
        except (KeyError, TypeError):
            continue
    return result
