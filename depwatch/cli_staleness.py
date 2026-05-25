"""CLI sub-command: depwatch staleness — report stale packages."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.config import load_config
from depwatch.digest import build_all_digests
from depwatch.runner import _collect_updates
from depwatch.staleness import evaluate_all, _DEFAULT_STALE_DAYS


def add_staleness_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("staleness", help="Report stale package versions")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--stale-days",
        type=int,
        default=_DEFAULT_STALE_DAYS,
        help="Days without a newer release before a package is considered stale",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--stale-only",
        action="store_true",
        help="Only show stale packages",
    )
    p.set_defaults(func=_run_staleness)


def _run_staleness(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1

    config = load_config(config_path)
    updates = _collect_updates(config)
    digests = build_all_digests(config, updates)
    report = evaluate_all(digests, stale_days=args.stale_days)

    entries = report.stale_only() if args.stale_only else report.entries

    if args.format == "json":
        payload = {
            "stale_days_threshold": args.stale_days,
            "total": len(report.entries),
            "stale_count": len(report.stale_only()),
            "entries": [e.to_dict() for e in entries],
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not entries:
        print("No packages to report.")
        return 0

    for e in entries:
        flag = " [STALE]" if e.stale else ""
        print(
            f"{e.project}/{e.package} ({e.language}): "
            f"{e.current_version} -> {e.latest_version}, "
            f"{e.days_since_release}d since release{flag}"
        )
    return 0
