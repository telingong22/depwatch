"""Runner: orchestrates one full check cycle and optional file-change watching."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from depwatch.checker import UpdateInfo, check_project
from depwatch.config import Config, ProjectConfig
from depwatch.digest import ProjectDigest, build_all_digests
from depwatch.notifier import DigestPayload, notify
from depwatch.reporter import build_report, format_report_text, write_report
from depwatch.state import get_last_seen, set_last_seen
from depwatch.watcher import FileWatcher

log = logging.getLogger(__name__)


def _collect_updates(
    project: ProjectConfig,
    state: dict,
) -> List[UpdateInfo]:
    """Return updates for *project* that have not been seen before."""
    all_updates = check_project(project)
    new_updates: List[UpdateInfo] = []
    for update in all_updates:
        last = get_last_seen(state, project.name, update.package)
        if last != update.latest_version:
            new_updates.append(update)
    return new_updates


def _digests_to_payload(digests: List[ProjectDigest]) -> DigestPayload:
    """Flatten non-empty digests into a single DigestPayload."""
    payload = DigestPayload()
    for digest in digests:
        if not digest.is_empty():
            payload.projects.append(digest)
    return payload


def run_cycle(
    config: Config,
    state: dict,
    report_path: Optional[str] = None,
) -> DigestPayload:
    """Run one full check cycle: fetch updates, build digests, optionally report."""
    updates_by_project: Dict[str, List[UpdateInfo]] = {}

    for project in config.projects:
        log.info("Checking project: %s", project.name)
        try:
            updates = _collect_updates(project, state)
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to check project %s: %s", project.name, exc)
            updates = []
        updates_by_project[project.name] = updates

        for update in updates:
            set_last_seen(state, project.name, update.package, update.latest_version)

    digests = build_all_digests(config.projects, updates_by_project)
    payload = _digests_to_payload(digests)

    if report_path:
        report = build_report(digests)
        write_report(report, report_path)
        log.info("Report written to %s", report_path)
        log.info("%s", format_report_text(report))

    return payload


def run_once(config: Config, state: dict, report_path: Optional[str] = None) -> None:
    """Run a single cycle and dispatch notifications."""
    payload = run_cycle(config, state, report_path=report_path)
    if not payload.is_empty():
        notify(config.alert, payload)
    else:
        log.info("No new dependency updates found.")


def make_file_watcher(config: Config) -> FileWatcher:
    """Create a FileWatcher that monitors all dependency files in *config*."""
    paths = [p.path for p in config.projects]
    return FileWatcher(paths)
