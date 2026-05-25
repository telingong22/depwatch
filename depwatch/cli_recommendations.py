"""CLI subcommand: depwatch recommendations — show upgrade recommendations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.config import Config
from depwatch.digest import build_all_digests
from depwatch.recommendations import build_recommendations


def add_recommendations_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "recommendations",
        help="Show prioritised upgrade recommendations for all projects",
    )
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--priority",
        choices=["high", "medium", "low", "all"],
        default="all",
        help="Filter by priority level",
    )
    p.set_defaults(func=_run_recommendations)


def _run_recommendations(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1

    config = Config.from_file(str(config_path))
    digests = build_all_digests(config)
    report = build_recommendations(digests)

    items = report.items
    if args.priority != "all":
        items = report.by_priority(args.priority)

    if args.format == "json":
        out = report.to_dict()
        if args.priority != "all":
            out["items"] = [r.to_dict() for r in items]
        print(json.dumps(out, indent=2))
        return 0

    if not items:
        print("No recommendations.")
        return 0

    for rec in items:
        print(str(rec))
    return 0
