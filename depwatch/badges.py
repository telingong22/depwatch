"""Generate status badge data for monitored projects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.digest import ProjectDigest


_COLOUR_UP_TO_DATE = "brightgreen"
_COLOUR_OUTDATED = "orange"
_COLOUR_MAJOR = "red"
_COLOUR_UNKNOWN = "lightgrey"


@dataclass
class BadgeInfo:
    project: str
    label: str
    message: str
    colour: str

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "label": self.label,
            "message": self.message,
            "colour": self.colour,
            "schemaVersion": 1,
        }

    def to_shields_url(self) -> str:
        """Return a shields.io endpoint-badge compatible URL fragment."""
        return (
            f"https://img.shields.io/badge/"
            f"{_encode(self.label)}-{_encode(self.message)}-{self.colour}"
        )


def _encode(text: str) -> str:
    """Minimal URL encoding for badge label/message segments."""
    return text.replace("-", "--").replace("_", "__").replace(" ", "_")


def _colour_for_digest(digest: ProjectDigest) -> str:
    if digest.is_empty():
        return _COLOUR_UP_TO_DATE
    for update in digest.updates:
        current = update.current_version or ""
        latest = update.latest_version or ""
        if current and latest:
            cur_major = current.lstrip("v").split(".")[0]
            lat_major = latest.lstrip("v").split(".")[0]
            if cur_major != lat_major:
                return _COLOUR_MAJOR
    return _COLOUR_OUTDATED


def build_badge(digest: ProjectDigest) -> BadgeInfo:
    """Build a BadgeInfo for a single project digest."""
    count = len(digest.updates)
    if count == 0:
        message = "up to date"
    elif count == 1:
        message = "1 update"
    else:
        message = f"{count} updates"

    return BadgeInfo(
        project=digest.project,
        label="depwatch",
        message=message,
        colour=_colour_for_digest(digest),
    )


def build_all_badges(digests: List[ProjectDigest]) -> List[BadgeInfo]:
    """Build badge info for every project digest."""
    return [build_badge(d) for d in digests]
