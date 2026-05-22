"""Configuration loading and validation for depwatch."""

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class ProjectConfig:
    name: str
    path: str
    language: str  # 'python' or 'go'

    def __post_init__(self):
        if self.language not in ("python", "go"):
            raise ValueError(f"Unsupported language '{self.language}' for project '{self.name}'")
        if not os.path.exists(self.path):
            raise ValueError(f"Project path does not exist: {self.path}")


@dataclass
class AlertConfig:
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    digest_interval_hours: int = 24

    def __post_init__(self):
        if self.digest_interval_hours < 1:
            raise ValueError("digest_interval_hours must be at least 1")
        if not self.email and not self.webhook_url:
            raise ValueError("At least one alert target (email or webhook_url) must be configured")


@dataclass
class Config:
    projects: List[ProjectConfig] = field(default_factory=list)
    alerts: AlertConfig = field(default_factory=lambda: AlertConfig(email="admin@example.com"))
    check_interval_hours: int = 6

    def __post_init__(self):
        if not self.projects:
            raise ValueError("At least one project must be configured")
        if self.check_interval_hours < 1:
            raise ValueError("check_interval_hours must be at least 1")


def load_config(path: str = "depwatch.yml") -> Config:
    """Load and parse configuration from a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    projects = [
        ProjectConfig(
            name=p["name"],
            path=p["path"],
            language=p["language"],
        )
        for p in raw.get("projects", [])
    ]

    raw_alerts = raw.get("alerts", {})
    alerts = AlertConfig(
        email=raw_alerts.get("email"),
        webhook_url=raw_alerts.get("webhook_url"),
        digest_interval_hours=raw_alerts.get("digest_interval_hours", 24),
    )

    return Config(
        projects=projects,
        alerts=alerts,
        check_interval_hours=raw.get("check_interval_hours", 6),
    )
