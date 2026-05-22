"""Configuration dataclasses and YAML loader for depwatch."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml


SUPPORTED_LANGUAGES = {"python", "go"}
VALID_INTERVALS = {"hourly", "daily", "weekly"}


@dataclass
class ProjectConfig:
    name: str
    language: str
    path: str
    dependencies: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{self.language}'. "
                f"Choose from: {SUPPORTED_LANGUAGES}"
            )
        if not os.path.exists(self.path):
            raise ValueError(f"Project path does not exist: {self.path}")


@dataclass
class AlertConfig:
    target: str
    interval: str = "daily"
    only_outdated: bool = True

    def __post_init__(self) -> None:
        if not self.target:
            raise ValueError("AlertConfig.target must not be empty.")
        if self.interval not in VALID_INTERVALS:
            raise ValueError(
                f"Invalid interval '{self.interval}'. "
                f"Choose from: {VALID_INTERVALS}"
            )


@dataclass
class Config:
    projects: list[ProjectConfig]
    alert: AlertConfig

    def __post_init__(self) -> None:
        if not self.projects:
            raise ValueError("Config must contain at least one project.")


def _parse_project(data: dict[str, Any]) -> ProjectConfig:
    return ProjectConfig(
        name=data["name"],
        language=data["language"],
        path=data["path"],
        dependencies=data.get("dependencies", {}),
    )


def _parse_alert(data: dict[str, Any]) -> AlertConfig:
    return AlertConfig(
        target=data["target"],
        interval=data.get("interval", "daily"),
        only_outdated=data.get("only_outdated", True),
    )


def load_config(path: str = "depwatch.yml") -> Config:
    """Load and parse the depwatch YAML configuration file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh)

    projects = [_parse_project(p) for p in raw.get("projects", [])]
    alert = _parse_alert(raw["alert"])
    return Config(projects=projects, alert=alert)
