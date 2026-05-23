"""CLI sub-command: depwatch filter — preview which updates would be suppressed."""
from __future__ import annotations

import argparse
import sys
from typing import List

from depwatch.config import load_config
from depwatch.filter import FilterConfig, apply_filter
from depwatch.runner import _collect_updates


def add_filter_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "filter",
        help="Preview which pending updates pass the current filter rules.",
    )
    p.add_argument("--config", default="depwatch.yml", help="Path to config file.")
    p.add_argument(
        "--ignore",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Glob pattern to ignore (repeatable).",
    )
    p.add_argument(
        "--min-bump",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Minimum version bump level to surface (default: patch).",
    )
    p.set_defaults(func=_run_filter)


def _run_filter(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    filter_cfg = FilterConfig(
        ignore_packages=args.ignore,
        min_bump=args.min_bump,
    )

    all_updates = _collect_updates(cfg)
    kept = apply_filter(all_updates, filter_cfg)
    suppressed = [u for u in all_updates if u not in kept]

    if not all_updates:
        print("No pending updates found.")
        return 0

    if kept:
        print(f"Updates that PASS the filter ({len(kept)}):")
        for u in kept:
            print(f"  {u.package}: {u.current_version} → {u.latest_version}")
    else:
        print("No updates pass the current filter.")

    if suppressed:
        print(f"\nUpdates SUPPRESSED by filter ({len(suppressed)}):")
        for u in suppressed:
            print(f"  {u.package}: {u.current_version} → {u.latest_version}")

    return 0
