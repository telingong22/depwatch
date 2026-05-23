"""CLI sub-command: prune stale history entries."""
from __future__ import annotations

import argparse
import os
import sys

from depwatch.retention import RetentionPolicy, prune_history

_DEFAULT_HISTORY = "depwatch_history.json"


def add_retention_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("prune", help="Prune history entries older than max-days")
    p.add_argument(
        "--history",
        default=_DEFAULT_HISTORY,
        help="Path to history JSON file (default: %(default)s)",
    )
    p.add_argument(
        "--max-days",
        type=int,
        default=90,
        dest="max_days",
        help="Retain entries newer than this many days (default: %(default)s)",
    )
    p.set_defaults(func=_run_retention)


def _run_retention(args: argparse.Namespace) -> None:
    if not os.path.exists(args.history):
        print(f"History file not found: {args.history}", file=sys.stderr)
        sys.exit(1)

    try:
        policy = RetentionPolicy(max_days=args.max_days)
    except ValueError as exc:
        print(f"Invalid retention policy: {exc}", file=sys.stderr)
        sys.exit(1)

    pruned = prune_history(args.history, policy)
    if pruned:
        print(f"Pruned {pruned} stale entr{'y' if pruned == 1 else 'ies'} from {args.history}.")
    else:
        print("Nothing to prune.")
