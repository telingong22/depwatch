"""CLI sub-command: depwatch trending — show most frequently updated packages."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.history import load_history
from depwatch.trending import build_trend_report


def add_trending_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("trending", help="Show most frequently updated packages")
    p.add_argument(
        "--history",
        default="depwatch_history.json",
        help="Path to history file (default: depwatch_history.json)",
    )
    p.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top packages to show (default: 5)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=_run_trending)


def _run_trending(args: argparse.Namespace) -> int:
    history_path = Path(args.history)
    if not history_path.exists():
        print(f"History file not found: {history_path}", file=sys.stderr)
        return 1

    top_n: int = args.top
    if top_n < 1:
        print("--top must be at least 1", file=sys.stderr)
        return 1

    history = load_history(history_path)
    report = build_trend_report(history, top_n=top_n)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.to_text())

    return 0
