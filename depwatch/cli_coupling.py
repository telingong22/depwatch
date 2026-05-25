"""CLI sub-command: depwatch coupling — show packages shared across projects."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import Config
from depwatch.runner import _collect_updates
from depwatch.digest import build_all_digests
from depwatch.coupling import build_coupling_report


def add_coupling_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "coupling",
        help="Show packages that appear in more than one project.",
    )
    p.add_argument("--config", default="depwatch.yml", help="Path to config file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    p.set_defaults(func=_run_coupling)


def _run_coupling(ns: argparse.Namespace) -> int:
    try:
        cfg = Config.from_file(ns.config)
    except FileNotFoundError:
        print(f"Config file not found: {ns.config}", file=sys.stderr)
        return 1

    updates_by_project = _collect_updates(cfg)
    digests = build_all_digests(cfg, updates_by_project)
    report = build_coupling_report(digests)

    if ns.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.summary())

    return 0
