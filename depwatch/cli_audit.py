"""CLI sub-command: depwatch audit — view the audit log."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from depwatch.audit import DEFAULT_AUDIT_PATH, load_audit


def add_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="Display the depwatch audit log")
    p.add_argument(
        "--audit-file",
        default=str(DEFAULT_AUDIT_PATH),
        help="Path to audit log file (default: %(default)s)",
    )
    p.add_argument(
        "--action",
        default=None,
        help="Filter entries by action type (e.g. email_sent)",
    )
    p.add_argument(
        "--project",
        default=None,
        help="Filter entries by project name",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.set_defaults(func=_run_audit)


def _run_audit(args: argparse.Namespace) -> int:
    path = Path(args.audit_file)
    if not path.exists():
        print(f"Audit file not found: {path}")
        return 1

    entries = load_audit(path)

    if args.action:
        entries = [e for e in entries if e.action == args.action]
    if args.project:
        entries = [e for e in entries if e.project == args.project]

    if not entries:
        print("No audit entries found.")
        return 0

    if args.fmt == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            print(
                f"[{e.timestamp}] {e.action:20s}  "
                f"{e.project}/{e.package}  "
                f"{e.current_version} -> {e.latest_version}"
                + (f"  ({e.detail})" if e.detail else "")
            )
    return 0
