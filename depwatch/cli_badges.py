"""CLI sub-command: generate badge data for projects."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.badges import build_all_badges
from depwatch.config import load_config
from depwatch.digest import build_all_digests
from depwatch.fetcher import fetch_all
from depwatch.parser import parse_dependencies
from depwatch.state import get_last_seen


def add_badges_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("badges", help="Generate status badge data for projects")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--format",
        choices=["json", "text", "shields"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=_run_badges)


def _run_badges(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 1

    all_deps = {
        project.name: parse_dependencies(project)
        for project in config.projects
    }
    releases = fetch_all(all_deps, config.projects)
    last_seen = {
        project.name: {
            pkg: get_last_seen(config.state_file, project.name, pkg)
            for pkg in all_deps.get(project.name, {})
        }
        for project in config.projects
    }
    digests = build_all_digests(config.projects, all_deps, releases, last_seen)
    badges = build_all_badges(digests)

    if args.format == "json":
        print(json.dumps([b.to_dict() for b in badges], indent=2))
    elif args.format == "shields":
        for badge in badges:
            print(f"{badge.project}: {badge.to_shields_url()}")
    else:
        if not badges:
            print("No projects configured.")
        for badge in badges:
            print(f"{badge.project}: {badge.message} [{badge.colour}]")

    return 0
