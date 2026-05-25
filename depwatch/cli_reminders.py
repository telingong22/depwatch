"""CLI sub-command: reminders — show packages overdue for an update."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from depwatch.reminders import get_overdue, load_reminders


def add_reminders_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("reminders", help="List packages overdue for an update")
    p.add_argument("--store", default=".depwatch_reminders.json", help="Reminder store file")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    p.set_defaults(func=_run_reminders)


def _run_reminders(ns: argparse.Namespace) -> int:
    store_path = Path(ns.store)
    if not store_path.exists():
        print(f"No reminder store found at {store_path}")
        return 0

    store = load_reminders(store_path)
    overdue = get_overdue(store)

    if not overdue:
        if ns.fmt == "json":
            print(json.dumps([]))
        else:
            print("No overdue reminders.")
        return 0

    if ns.fmt == "json":
        print(json.dumps([e.to_dict() for e in overdue], indent=2))
    else:
        print(f"Overdue reminders ({len(overdue)}):")
        for e in overdue:
            print(
                f"  [{e.language}] {e.project} / {e.package}  "
                f"latest={e.latest}  first_seen={e.first_seen}  "
                f"threshold={e.reminder_days}d"
            )
    return 0
