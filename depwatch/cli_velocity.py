"""CLI sub-command: depwatch velocity — show package update velocity."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from depwatch.config import load_config
from depwatch.digest import build_all_digests
from depwatch.runner import _collect_updates
from depwatch.velocity import VelocityReport, build_velocity


def add_velocity_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("velocity", help="Show package update velocity")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show top N fastest-moving packages (default: 10)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=_run_velocity)


def _print_text(report: VelocityReport, top: int) -> None:
    fastest = report.fastest(top)
    if not fastest:
        print("No velocity data available.")
        return
    print(f"Top {top} fastest-moving packages:")
    for i, entry in enumerate(fastest, 1):
        print(f"  {i:>3}. {entry}")


def _run_velocity(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 1

    updates_by_project = _collect_updates(config)
    digests = build_all_digests(config.projects, updates_by_project)
    report = build_velocity(digests)

    top = getattr(args, "top", 10)
    fmt = getattr(args, "format", "text")

    if fmt == "json":
        data = report.to_dict()
        data["fastest"] = report.fastest(top)
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_text(report, top)

    return 0
