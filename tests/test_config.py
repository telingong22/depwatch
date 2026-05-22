"""Tests for depwatch configuration loading and validation."""

import os
import textwrap
import pytest

from depwatch.config import AlertConfig, Config, ProjectConfig, load_config


# ---------------------------------------------------------------------------
# Unit tests for dataclasses
# ---------------------------------------------------------------------------

def test_project_config_invalid_language():
    with pytest.raises(ValueError, match="Unsupported language"):
        ProjectConfig(name="x", path=".", language="ruby")


def test_project_config_invalid_path():
    with pytest.raises(ValueError, match="does not exist"):
        ProjectConfig(name="x", path="/nonexistent/path", language="python")


def test_alert_config_requires_target():
    with pytest.raises(ValueError, match="At least one alert target"):
        AlertConfig()


def test_alert_config_invalid_interval():
    with pytest.raises(ValueError, match="digest_interval_hours"):
        AlertConfig(email="a@b.com", digest_interval_hours=0)


def test_config_requires_projects():
    with pytest.raises(ValueError, match="At least one project"):
        Config(projects=[], alerts=AlertConfig(email="a@b.com"))


# ---------------------------------------------------------------------------
# Integration tests for load_config
# ---------------------------------------------------------------------------

@pytest.fixture()
def config_file(tmp_path):
    """Create a minimal valid config file and return its path."""
    project_dir = tmp_path / "app"
    project_dir.mkdir()

    cfg = textwrap.dedent(f"""\
        check_interval_hours: 4
        projects:
          - name: test-app
            path: {project_dir}
            language: python
        alerts:
          email: test@example.com
          digest_interval_hours: 12
    """)
    cfg_path = tmp_path / "depwatch.yml"
    cfg_path.write_text(cfg)
    return str(cfg_path)


def test_load_config_success(config_file):
    config = load_config(config_file)
    assert config.check_interval_hours == 4
    assert len(config.projects) == 1
    assert config.projects[0].name == "test-app"
    assert config.projects[0].language == "python"
    assert config.alerts.email == "test@example.com"
    assert config.alerts.digest_interval_hours == 12


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/tmp/does_not_exist_depwatch.yml")
