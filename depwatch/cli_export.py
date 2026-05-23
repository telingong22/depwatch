"""CLI helpers for the ``depwatch export`` sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from depwatch.config import load_config
from depwatch.exporter import export_report
from depwatch.reporter import Report
from depwatch.runner import run_once as runner_run_once


def add_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command on *subparsers*."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "export",
        help="Run a single check cycle and export the report.",
    )
    p.add_argument(
        "--config",
        default="depwatch.yml",
        metavar="FILE",
        help="Path to configuration file (default: depwatch.yml).",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["json", "markdown", "md"],
        default="json",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--output",
        required=True,
        metavar="FILE",
        help="Destination file path for the exported report.",
    )
    p.set_defaults(func=_run_export)


def _run_export(args: argparse.Namespace) -> int:
    """Entry point for the *export* sub-command."""
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1

    cfg = load_config(config_path)
    report: Report = runner_run_once(cfg)

    try:
        export_report(report, args.fmt, args.output)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Report written to {args.output}")
    return 0
