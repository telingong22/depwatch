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


def _print_update_list(header: str, updates: list) -> None:
    """Print a labelled list of package updates to stdout."""
    print(header)
    for u in updates:
        print(f"  {u.package}: {u.current_version} \u2192 {u.latest_version}")


def _run_filter(args: argparse.Namespace) -> int:
    """Execute the filter sub-command and return an exit code."""
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
        _print_update_list(f"Updates that PASS the filter ({len(kept)}):", kept)
    else:
        print("No updates pass the current filter.")

    if suppressed:
        print()
        _print_update_list(f"Updates SUPPRESSED by filter ({len(suppressed)}):", suppressed)

    return 0
