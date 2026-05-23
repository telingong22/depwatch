"""High-level run loop: fetch → check → digest → notify → persist state."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from depwatch.checker import UpdateInfo, check_project
from depwatch.config import Config, ProjectConfig
from depwatch.digest import ProjectDigest, build_all_digests
from depwatch.notifier import DigestPayload, notify
from depwatch.state import StateDict, load_state, save_state

logger = logging.getLogger(__name__)

_STATE_PATH = Path(".depwatch_state.json")


def _collect_updates(projects: List[ProjectConfig]) -> dict:
    """Return mapping of project → list of UpdateInfo."""
    results = {}
    for project in projects:
        try:
            updates: List[UpdateInfo] = check_project(project)
            results[project] = updates
            logger.info(
                "Project '%s': %d package(s) checked, %d update(s) found.",
                project.name,
                len(updates),
                sum(1 for u in updates if u.latest_version != u.current_version),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error checking project '%s': %s", project.name, exc)
            results[project] = []
    return results


def _digests_to_payload(digests: List[ProjectDigest], cfg: Config) -> DigestPayload:
    """Flatten non-empty digests into a single :class:`DigestPayload`."""
    all_updates: List[UpdateInfo] = []
    for digest in digests:
        all_updates.extend(digest.updates)
    return DigestPayload(updates=all_updates, alert_config=cfg.alert)


def run_cycle(cfg: Config, state: StateDict) -> None:
    """Execute one full check-and-notify cycle, mutating *state* in place."""
    logger.info("Starting dependency check cycle for %d project(s).", len(cfg.projects))

    updates_map = _collect_updates(cfg.projects)
    digests = build_all_digests(updates_map, state)

    non_empty = [d for d in digests if not d.is_empty]
    if not non_empty:
        logger.info("No new updates found this cycle.")
        return

    payload = _digests_to_payload(non_empty, cfg)
    notify(payload)


def run_once(cfg: Config, state_path: Path = _STATE_PATH) -> None:
    """Load state, run one cycle, and persist updated state."""
    state = load_state(state_path)
    try:
        run_cycle(cfg, state)
    finally:
        save_state(state, state_path)
