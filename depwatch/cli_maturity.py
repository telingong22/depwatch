"""CLI sub-command: depwatch maturity

Prints a maturity report for all dependency updates found in the current
cycle, showing how "fresh" or "mature" each new release is.
"""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import load_config
from depwatch.runner import run_once
from depwatch.digest import build_all_digests
from depwatch.maturity import build_maturity_report


def add_maturity_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "maturity",
        help="Show maturity scores for pending dependency updates.",
    )
    p.add_argument("--config", default="depwatch.yml", help="Path to config file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    p.add_argument(
        "--label",
        default=None,
        help="Filter results to a specific maturity label.",
    )
    p.set_defaults(func=_run_maturity)


def _run_maturity(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    updates = run_once(cfg)
    digests = build_all_digests(cfg, updates)
    report = build_maturity_report(digests)

    scores = report.scores
    if args.label:
        scores = report.by_label(args.label)

    if args.format == "json":
        print(json.dumps({"scores": [s.to_dict() for s in scores]}, indent=2))
        return 0

    if not scores:
        print("No maturity data available.")
        return 0

    for score in scores:
        print(str(score))
    return 0
