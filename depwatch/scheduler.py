"""Scheduler: periodically runs dependency checks and triggers notifications."""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from depwatch.checker import check_project
from depwatch.config import Config
from depwatch.notifier import DigestPayload, notify

logger = logging.getLogger(__name__)


class Scheduler:
    """Runs check-and-notify cycles based on alert interval config."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._last_run: Optional[datetime] = None
        self._running = False

    @property
    def interval_seconds(self) -> int:
        unit = self.config.alert.interval_unit
        value = self.config.alert.interval_value
        units = {"minutes": 60, "hours": 3600, "days": 86400}
        return value * units.get(unit, 3600)

    def _is_due(self) -> bool:
        if self._last_run is None:
            return True
        return datetime.utcnow() >= self._last_run + timedelta(seconds=self.interval_seconds)

    def run_once(self) -> DigestPayload:
        """Run a single check cycle across all projects and notify if updates found."""
        logger.info("Running dependency check cycle")
        payload = DigestPayload(updates={})

        for project in self.config.projects:
            updates = check_project(project)
            if updates:
                payload.updates[project.name] = updates
                logger.info(
                    "Project '%s': %d update(s) found", project.name, len(updates)
                )
            else:
                logger.debug("Project '%s': no updates", project.name)

        if not payload.is_empty():
            notify(self.config.alert, payload)
        else:
            logger.info("No updates found across all projects")

        self._last_run = datetime.utcnow()
        return payload

    def start(self) -> None:
        """Block and run check cycles on the configured interval."""
        self._running = True
        logger.info(
            "Scheduler started (interval: %d seconds)", self.interval_seconds
        )
        while self._running:
            if self._is_due():
                try:
                    self.run_once()
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("Check cycle failed: %s", exc)
            time.sleep(10)

    def stop(self) -> None:
        """Signal the scheduler loop to stop."""
        self._running = False
        logger.info("Scheduler stopped")
