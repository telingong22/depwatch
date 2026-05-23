"""High-level run loop: collects updates, builds digests, and notifies.

Also integrates FileWatcher so that a change to a dependency file
triggers an immediate cycle in addition to the scheduled one.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from depwatch.checker import UpdateInfo, check_project
from depwatch.config import Config, ProjectConfig
from depwatch.digest import ProjectDigest, build_all_digests
from depwatch.notifier import DigestPayload, notify
from depwatch.state import get_last_seen, set_last_seen
from depwatch.watcher import FileWatcher

logger = logging.getLogger(__name__)


def _collect_updates(project: ProjectConfig) -> List[UpdateInfo]:
    updates = check_project(project)
    new_updates: List[UpdateInfo] = []
    for u in updates:
        last = get_last_seen(project.name, u.package)
        if last is None or u.latest_version != last:
            new_updates.append(u)
            set_last_seen(project.name, u.package, u.latest_version)
    return new_updates


def _digests_to_payload(digests: List[ProjectDigest]) -> DigestPayload:
    payload = DigestPayload()
    for d in digests:
        if not d.is_empty():
            payload.projects.append(d)
    return payload


def run_cycle(config: Config) -> None:
    """Run one full check-and-notify cycle for all configured projects."""
    all_updates = {p.name: _collect_updates(p) for p in config.projects}
    digests = build_all_digests(config.projects, all_updates)
    payload = _digests_to_payload(digests)
    if not payload.is_empty():
        notify(config.alert, payload)
    else:
        logger.info("No new updates found in this cycle")


def run_once(config: Config) -> None:
    """Run a single cycle (used for --once CLI flag)."""
    run_cycle(config)


def make_file_watcher(config: Config, callback) -> FileWatcher:
    """Build a FileWatcher covering all dependency files in *config*."""
    paths = [Path(p.path) for p in config.projects]
    return FileWatcher(paths, callback)
