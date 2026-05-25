"""CLI sub-command: depwatch approval — approve/reject/list dependency updates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.approval import (
    ApprovalRecord,
    filter_unapproved,
    get_status,
    load_approvals,
    set_approval,
)
from depwatch.checker import UpdateInfo


def add_approval_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("approval", help="Manage update approvals")
    p.add_argument(
        "cmd",
        choices=["approve", "reject", "list", "status"],
        help="Action to perform",
    )
    p.add_argument("--project", default="", help="Project name")
    p.add_argument("--package", default="", help="Package name")
    p.add_argument("--version", default="", help="Package version")
    p.add_argument("--author", default="depwatch", help="Who is approving/rejecting")
    p.add_argument("--note", default="", help="Optional note")
    p.add_argument(
        "--file",
        default="depwatch_approvals.json",
        help="Path to approvals file",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=_run_approval)


def _run_approval(args: argparse.Namespace) -> int:
    path = Path(args.file)

    if args.cmd in ("approve", "reject"):
        if not args.project or not args.package or not args.version:
            print("Error: --project, --package, and --version are required.", file=sys.stderr)
            return 1
        status = "approved" if args.cmd == "approve" else "rejected"
        # Build a minimal UpdateInfo-compatible object
        update = UpdateInfo(
            project=args.project,
            package=args.package,
            current="",
            latest=args.version,
            language="python",
        )
        rec = set_approval(update, status=status, author=args.author, note=args.note, path=path)
        if args.format == "json":
            print(json.dumps(rec.to_dict(), indent=2))
        else:
            print(f"[{rec.status.upper()}] {rec.project}/{rec.package}=={rec.version} by {rec.author}")
        return 0

    if args.cmd == "list":
        records = load_approvals(path)
        if args.format == "json":
            print(json.dumps([r.to_dict() for r in records.values()], indent=2))
        else:
            if not records:
                print("No approval records found.")
            for rec in records.values():
                print(f"[{rec.status.upper():8}] {rec.project}/{rec.package}=={rec.version}  ({rec.author})")
        return 0

    if args.cmd == "status":
        if not args.project or not args.package or not args.version:
            print("Error: --project, --package, and --version are required.", file=sys.stderr)
            return 1
        update = UpdateInfo(
            project=args.project,
            package=args.package,
            current="",
            latest=args.version,
            language="python",
        )
        rec = get_status(update, path=path)
        if rec is None:
            print("pending (no record)")
        elif args.format == "json":
            print(json.dumps(rec.to_dict(), indent=2))
        else:
            print(f"[{rec.status.upper()}] note: {rec.note or '—'}")
        return 0

    return 0
