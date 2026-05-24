"""Labeling module: attach human-readable labels/tags to dependency updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import UpdateInfo
from depwatch.filter import _bump_level


# Well-known labels
LABEL_SECURITY = "security"
LABEL_MAJOR = "major-bump"
LABEL_MINOR = "minor-bump"
LABEL_PATCH = "patch-bump"
LABEL_PRE_RELEASE = "pre-release"
LABEL_GO = "go"
LABEL_PYTHON = "python"

_PRE_RELEASE_MARKERS = ("a", "b", "rc", "alpha", "beta", "dev", "post")


@dataclass
class LabeledUpdate:
    update: UpdateInfo
    labels: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.update.project_name,
            "package": self.update.package_name,
            "current": self.update.current_version,
            "latest": self.update.latest_version,
            "labels": self.labels,
        }


def _is_pre_release(version: str) -> bool:
    v = version.lstrip("v").lower()
    return any(marker in v for marker in _PRE_RELEASE_MARKERS)


def label_update(update: UpdateInfo, security_packages: List[str] | None = None) -> LabeledUpdate:
    """Derive labels for a single update."""
    labels: List[str] = []

    # Language label
    if update.language == "python":
        labels.append(LABEL_PYTHON)
    elif update.language == "go":
        labels.append(LABEL_GO)

    # Bump level
    level = _bump_level(update.current_version, update.latest_version)
    if level == "major":
        labels.append(LABEL_MAJOR)
    elif level == "minor":
        labels.append(LABEL_MINOR)
    elif level == "patch":
        labels.append(LABEL_PATCH)

    # Pre-release
    if _is_pre_release(update.latest_version):
        labels.append(LABEL_PRE_RELEASE)

    # Security
    if security_packages and update.package_name.lower() in [
        p.lower() for p in security_packages
    ]:
        labels.append(LABEL_SECURITY)

    return LabeledUpdate(update=update, labels=labels)


def label_all(
    updates: List[UpdateInfo],
    security_packages: List[str] | None = None,
) -> List[LabeledUpdate]:
    """Label a list of updates."""
    return [label_update(u, security_packages) for u in updates]
