"""Build per-project update digests, filtering out already-seen versions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.checker import UpdateInfo
from depwatch.config import ProjectConfig
from depwatch.state import StateDict, get_last_seen, set_last_seen

logger = logging.getLogger(__name__)


@dataclass
class ProjectDigest:
    project_name: str
    updates: List[UpdateInfo] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.updates) == 0


def build_digest(
    project: ProjectConfig,
    updates: List[UpdateInfo],
    state: StateDict,
) -> ProjectDigest:
    """Return a :class:`ProjectDigest` containing only *new* updates.

    An update is considered *new* when the latest version differs from the
    last-seen version stored in *state*.  After filtering, *state* is updated
    in-place so that the same version is not reported again next cycle.
    """
    new_updates: List[UpdateInfo] = []
    for info in updates:
        last = get_last_seen(state, project.name, info.package)
        if last == info.latest_version:
            logger.debug(
                "%s/%s already seen at %s — skipping.",
                project.name,
                info.package,
                last,
            )
            continue
        new_updates.append(info)
        set_last_seen(state, project.name, info.package, info.latest_version)
        logger.info(
            "New release detected: %s/%s %s (was %s).",
            project.name,
            info.package,
            info.latest_version,
            last or "<unknown>",
        )

    return ProjectDigest(project_name=project.name, updates=new_updates)


def build_all_digests(
    projects_updates: Dict[ProjectConfig, List[UpdateInfo]],
    state: StateDict,
) -> List[ProjectDigest]:
    """Build digests for every project, skipping already-seen versions."""
    return [
        build_digest(project, updates, state)
        for project, updates in projects_updates.items()
    ]
