"""CLI sub-command: depwatch tag — apply tag rules to current updates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.config import load_config
from depwatch.runner import run_once
from depwatch.tagging import rules_from_config, tag_all


def add_tag_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tag", help="Tag dependency updates with custom labels")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--rules",
        default=None,
        help="JSON file containing tag rules [{pattern, tag}, ...]",
    )
    p.set_defaults(func=_run_tag)


def _run_tag(ns: argparse.Namespace) -> None:
    config_path = Path(ns.config)
    if not config_path.exists():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)

    raw_rules: list = []
    if ns.rules:
        rules_path = Path(ns.rules)
        if not rules_path.exists():
            print(f"error: rules file not found: {rules_path}", file=sys.stderr)
            sys.exit(1)
        raw_rules = json.loads(rules_path.read_text())

    rules = rules_from_config(raw_rules)
    updates = run_once(config)
    tagged = tag_all(updates, rules)

    if ns.format == "json":
        print(json.dumps([t.to_dict() for t in tagged], indent=2))
        return

    if not tagged:
        print("No updates found.")
        return

    for t in tagged:
        tag_str = ", ".join(t.tags) if t.tags else "(none)"
        print(
            f"[{t.update.language}] {t.update.project}/{t.update.package} "
            f"{t.update.current} -> {t.update.latest}  tags={tag_str}"
        )
