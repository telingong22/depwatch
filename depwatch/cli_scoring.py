"""CLI sub-command: ``depwatch score``.

Prints a ranked priority table of pending dependency updates.
"""

from __future__ import annotations

import argparse
import json
import sys

from depwatch.config import load_config
from depwatch.runner import _collect_updates
from depwatch.scoring import rank_updates


def add_scoring_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("score", help="Rank pending updates by priority score")
    p.add_argument("--config", default="depwatch.yml", help="Path to depwatch.yml")
    p.add_argument(
        "--security",
        nargs="*",
        metavar="PKG",
        default=[],
        help="Package names to treat as security-sensitive (+50 score)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        help="Limit output to top N results (0 = all)",
    )
    p.set_defaults(func=_run_scoring)


def _run_scoring(args: argparse.Namespace) -> None:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    updates = _collect_updates(cfg)
    ranked = rank_updates(updates, security_packages=args.security)

    if args.top > 0:
        ranked = ranked[:args.top]

    if not ranked:
        if args.format == "json":
            print(json.dumps([]))
        else:
            print("No pending updates.")
        return

    if args.format == "json":
        out = [
            {"update": {"package": u.package_name, "project": u.project_name,
                        "current": u.current_version, "latest": u.latest_version},
             "score": ps.to_dict()}
            for u, ps in ranked
        ]
        print(json.dumps(out, indent=2))
    else:
        header = f"{'#':<4} {'Package':<30} {'Project':<20} {'Current':<14} {'Latest':<14} {'Score':>6}"
        print(header)
        print("-" * len(header))
        for idx, (u, ps) in enumerate(ranked, 1):
            print(
                f"{idx:<4} {u.package_name:<30} {u.project_name:<20} "
                f"{u.current_version:<14} {u.latest_version:<14} {ps.score:>6}"
            )
