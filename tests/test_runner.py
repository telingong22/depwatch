"""Tests for depwatch.runner (including FileWatcher integration hook)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import UpdateInfo
from depwatch.config import AlertConfig, Config, ProjectConfig
from depwatch.digest import ProjectDigest
from depwatch.notifier import DigestPayload
from depwatch.runner import (
    _collect_updates,
    _digests_to_payload,
    make_file_watcher,
    run_cycle,
    run_once,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path) -> Config:
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.31.0\n")
    project = ProjectConfig(name="myapp", language="python", path=str(req))
    alert = AlertConfig(type="email", target="dev@example.com", interval="1h")
    return Config(projects=[project], alert=alert)


def _make_update(pkg="requests", current="2.31.0", latest="2.32.0") -> UpdateInfo:
    return UpdateInfo(package=pkg, current_version=current, latest_version=latest)


# ---------------------------------------------------------------------------
# _collect_updates
# ---------------------------------------------------------------------------

@patch("depwatch.runner.set_last_seen")
@patch("depwatch.runner.get_last_seen", return_value=None)
@patch("depwatch.runner.check_project")
def test_collect_updates_new(mock_check, mock_get, mock_set, tmp_path):
    config = _make_config(tmp_path)
    update = _make_update()
    mock_check.return_value = [update]
    result = _collect_updates(config.projects[0])
    assert result == [update]
    mock_set.assert_called_once_with("myapp", "requests", "2.32.0")


@patch("depwatch.runner.set_last_seen")
@patch("depwatch.runner.get_last_seen", return_value="2.32.0")
@patch("depwatch.runner.check_project")
def test_collect_updates_already_seen(mock_check, mock_get, mock_set, tmp_path):
    config = _make_config(tmp_path)
    mock_check.return_value = [_make_update()]
    result = _collect_updates(config.projects[0])
    assert result == []
    mock_set.assert_not_called()


# ---------------------------------------------------------------------------
# _digests_to_payload
# ---------------------------------------------------------------------------

def test_digests_to_payload_filters_empty():
    empty = ProjectDigest(project="a", updates=[])
    non_empty = ProjectDigest(project="b", updates=[_make_update()])
    payload = _digests_to_payload([empty, non_empty])
    assert len(payload.projects) == 1
    assert payload.projects[0].project == "b"


def test_digests_to_payload_all_empty():
    payload = _digests_to_payload([ProjectDigest(project="x", updates=[])])
    assert payload.is_empty()


# ---------------------------------------------------------------------------
# run_cycle / run_once
# ---------------------------------------------------------------------------

@patch("depwatch.runner.notify")
@patch("depwatch.runner.build_all_digests")
@patch("depwatch.runner.check_project", return_value=[])
@patch("depwatch.runner.get_last_seen", return_value=None)
def test_run_cycle_no_updates_skips_notify(mock_get, mock_check, mock_build, mock_notify, tmp_path):
    config = _make_config(tmp_path)
    mock_build.return_value = [ProjectDigest(project="myapp", updates=[])]
    run_cycle(config)
    mock_notify.assert_not_called()


@patch("depwatch.runner.notify")
@patch("depwatch.runner.build_all_digests")
@patch("depwatch.runner.set_last_seen")
@patch("depwatch.runner.get_last_seen", return_value=None)
@patch("depwatch.runner.check_project")
def test_run_cycle_with_updates_calls_notify(mock_check, mock_get, mock_set, mock_build, mock_notify, tmp_path):
    config = _make_config(tmp_path)
    update = _make_update()
    mock_check.return_value = [update]
    mock_build.return_value = [ProjectDigest(project="myapp", updates=[update])]
    run_cycle(config)
    mock_notify.assert_called_once()


# ---------------------------------------------------------------------------
# make_file_watcher
# ---------------------------------------------------------------------------

def test_make_file_watcher_returns_watcher(tmp_path):
    config = _make_config(tmp_path)
    cb = MagicMock()
    watcher = make_file_watcher(config, cb)
    # requirements.txt is a watched filename so it should be included
    assert len(watcher._paths) == 1
