"""Tests for depwatch.scheduler."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import UpdateInfo
from depwatch.config import AlertConfig, Config, ProjectConfig
from depwatch.notifier import DigestPayload
from depwatch.scheduler import Scheduler


def _make_config(interval_value: int = 1, interval_unit: str = "hours") -> Config:
    alert = AlertConfig(
        target="test@example.com",
        interval_value=interval_value,
        interval_unit=interval_unit,
    )
    project = ProjectConfig(name="myapp", language="python", path=".")
    return Config(projects=[project], alert=alert)


def _make_update() -> UpdateInfo:
    from depwatch.fetcher import ReleaseInfo
    return UpdateInfo(
        package="requests",
        current="2.28.0",
        latest=ReleaseInfo(version="2.31.0", url="https://pypi.org/project/requests/"),
    )


class TestSchedulerInterval:
    def test_interval_hours(self):
        s = Scheduler(_make_config(interval_value=2, interval_unit="hours"))
        assert s.interval_seconds == 7200

    def test_interval_minutes(self):
        s = Scheduler(_make_config(interval_value=30, interval_unit="minutes"))
        assert s.interval_seconds == 1800

    def test_interval_days(self):
        s = Scheduler(_make_config(interval_value=1, interval_unit="days"))
        assert s.interval_seconds == 86400

    def test_interval_unknown_unit_defaults_to_hour(self):
        s = Scheduler(_make_config(interval_value=3, interval_unit="weeks"))
        assert s.interval_seconds == 10800


class TestSchedulerIsDue:
    def test_is_due_on_first_run(self):
        s = Scheduler(_make_config())
        assert s._is_due() is True

    def test_not_due_after_recent_run(self):
        s = Scheduler(_make_config(interval_value=1, interval_unit="hours"))
        s._last_run = datetime.utcnow()
        assert s._is_due() is False

    def test_due_after_interval_elapsed(self):
        s = Scheduler(_make_config(interval_value=1, interval_unit="hours"))
        s._last_run = datetime.utcnow() - timedelta(hours=2)
        assert s._is_due() is True


class TestSchedulerRunOnce:
    @patch("depwatch.scheduler.notify")
    @patch("depwatch.scheduler.check_project")
    def test_run_once_with_updates_calls_notify(self, mock_check, mock_notify):
        update = _make_update()
        mock_check.return_value = [update]
        s = Scheduler(_make_config())
        payload = s.run_once()
        assert not payload.is_empty()
        mock_notify.assert_called_once()
        assert s._last_run is not None

    @patch("depwatch.scheduler.notify")
    @patch("depwatch.scheduler.check_project")
    def test_run_once_no_updates_skips_notify(self, mock_check, mock_notify):
        mock_check.return_value = []
        s = Scheduler(_make_config())
        payload = s.run_once()
        assert payload.is_empty()
        mock_notify.assert_not_called()

    @patch("depwatch.scheduler.notify")
    @patch("depwatch.scheduler.check_project", side_effect=RuntimeError("boom"))
    def test_start_handles_cycle_exception(self, mock_check, mock_notify):
        """start() should not crash on a failed cycle."""
        s = Scheduler(_make_config())
        call_count = 0

        original_is_due = s._is_due

        def limited_is_due():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                s.stop()
            return True

        s._is_due = limited_is_due
        with patch("depwatch.scheduler.time.sleep"):
            s.start()  # should not raise
        mock_notify.assert_not_called()
