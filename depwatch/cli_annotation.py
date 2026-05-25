"""CLI sub-command: manage annotations for dependency updates."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.annotation import AnnotationStore, annotate_update, load_annotations, save_annotations

_DEFAULT_PATH = ".depwatch/annotations.json"


def add_annotation_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("annotate", help="Manage dependency annotations")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Annotations file path")
    sub = p.add_subparsers(dest="annotation_cmd")

    add = sub.add_parser("add", help="Add an annotation")
    add.add_argument("--project", required=True)
    add.add_argument("--package", required=True)
    add.add_argument("--note", required=True)
    add.add_argument("--author", default="depwatch")

    lst = sub.add_parser("list", help="List annotations")
    lst.add_argument("--project", default=None)
    lst.add_argument("--package", default=None)
    lst.add_argument("--format", choices=["text", "json"], default="text")

    p.set_defaults(func=_run_annotation)


def _run_annotation(ns: argparse.Namespace) -> int:
    store = load_annotations(ns.file)

    if ns.annotation_cmd == "add":
        ann = annotate_update(store, ns.project, ns.package, ns.note, ns.author)
        save_annotations(store, ns.file)
        print(f"Annotation added: [{ann.project}] {ann.package} — {ann.note}")
        return 0

    if ns.annotation_cmd == "list":
        entries = store.entries
        if ns.project:
            entries = [e for e in entries if e.project == ns.project]
        if ns.package:
            entries = [e for e in entries if e.package == ns.package]

        if not entries:
            print("No annotations found.")
            return 0

        fmt = getattr(ns, "format", "text")
        if fmt == "json":
            print(json.dumps([e.to_dict() for e in entries], indent=2))
        else:
            for e in entries:
                print(f"[{e.project}] {e.package} ({e.author}): {e.note}")
        return 0

    print("No annotation sub-command given. Use 'add' or 'list'.", file=sys.stderr)
    return 1
