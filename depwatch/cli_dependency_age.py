"""CLI sub-command: depwatch age — show dependency age report."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import load_config
from depwatch.dependency_age import build_age_report
from depwatch.digest import build_all_digests
from depwatch.runner import _collect_updates
from depwatch.state import load_state


def add_age_parser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("age", help="Show dependency age statistics")
    p.add_argument("--config", default="depwatch.yml", help="Path to config file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--min-days",
        type=int,
        default=0,
        help="Only show entries older than N days",
    )
    p.set_defaults(func=_run_age)


def _run_age(ns: argparse.Namespace) -> int:
    try:
        cfg = load_config(ns.config)
    except FileNotFoundError:
        print(f"Config file not found: {ns.config}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    state = load_state()
    updates = _collect_updates(cfg, state)
    digests = build_all_digests(cfg.projects, updates)
    report = build_age_report(digests)

    min_days: int = ns.min_days
    entries = [e for e in report.oldest_first() if e.age_days >= min_days]

    if ns.format == "json":
        print(json.dumps({"entries": [e.to_dict() for e in entries]}, indent=2))
        return 0

    if not entries:
        print("No dependency age data available.")
        return 0

    for entry in entries:
        print(str(entry))
    return 0
