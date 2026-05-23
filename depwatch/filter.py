"""Filter updates based on user-defined rules (ignore lists, version constraints)."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Sequence

from depwatch.checker import UpdateInfo


@dataclass
class FilterConfig:
    """Rules that decide which updates to suppress."""

    ignore_packages: List[str] = field(default_factory=list)
    """Exact names or glob patterns, e.g. ['boto3', 'internal-*']."""

    min_bump: str = "patch"  # patch | minor | major
    """Minimum version-bump level required to surface an update."""


def _bump_level(current: str, latest: str) -> str:
    """Return 'major', 'minor', or 'patch' describing the version distance."""
    def _parts(v: str):
        parts = v.lstrip("v").split(".")
        result = []
        for p in parts[:3]:
            try:
                result.append(int(p))
            except ValueError:
                result.append(0)
        while len(result) < 3:
            result.append(0)
        return result

    c = _parts(current)
    l = _parts(latest)

    if l[0] != c[0]:
        return "major"
    if l[1] != c[1]:
        return "minor"
    return "patch"


_BUMP_ORDER = {"patch": 0, "minor": 1, "major": 2}


def _is_ignored(name: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch(name, pat) for pat in patterns)


def apply_filter(updates: Sequence[UpdateInfo], cfg: FilterConfig) -> List[UpdateInfo]:
    """Return only the updates that pass the filter rules."""
    min_level = _BUMP_ORDER.get(cfg.min_bump, 0)
    kept: List[UpdateInfo] = []
    for u in updates:
        if _is_ignored(u.package, cfg.ignore_packages):
            continue
        level = _bump_level(u.current_version, u.latest_version)
        if _BUMP_ORDER[level] >= min_level:
            kept.append(u)
    return kept
