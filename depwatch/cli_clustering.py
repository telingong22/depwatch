"""CLI sub-command: depwatch cluster — show update clusters."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import load_config
from depwatch.digest import build_all_digests
from depwatch.runner import _collect_updates
from depwatch.clustering import build_clusters


def add_clustering_parser(subparsers: argparse.Action) -> None:
    p = subparsers.add_parser(
        "cluster",
        help="Group pending updates into language/bump-level clusters.",
    )
    p.add_argument("--config", default="depwatch.yml", metavar="FILE")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )
    p.set_defaults(func=_run_clustering)


def _run_clustering(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    updates_by_project = _collect_updates(cfg)
    digests = build_all_digests(cfg, updates_by_project)
    report = build_clusters(digests)

    if args.fmt == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if report.is_empty():
            print("No updates to cluster.")
        else:
            print(report.summary())

    return 0
