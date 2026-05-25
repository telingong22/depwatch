"""Annotation module: attach human-readable notes to dependency updates."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Annotation:
    project: str
    package: str
    note: str
    author: str = "depwatch"

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "package": self.package,
            "note": self.note,
            "author": self.author,
        }

    @staticmethod
    def from_dict(data: dict) -> "Annotation":
        return Annotation(
            project=data["project"],
            package=data["package"],
            note=data["note"],
            author=data.get("author", "depwatch"),
        )


@dataclass
class AnnotationStore:
    entries: List[Annotation] = field(default_factory=list)

    def add(self, annotation: Annotation) -> None:
        self.entries.append(annotation)

    def get(self, project: str, package: str) -> List[Annotation]:
        return [
            e for e in self.entries
            if e.project == project and e.package == package
        ]

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def to_dict(self) -> dict:
        return {"annotations": [e.to_dict() for e in self.entries]}


def load_annotations(path: str) -> AnnotationStore:
    if not os.path.exists(path):
        return AnnotationStore()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, dict) or "annotations" not in raw:
            return AnnotationStore()
        return AnnotationStore(
            entries=[Annotation.from_dict(d) for d in raw["annotations"]]
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return AnnotationStore()


def save_annotations(store: AnnotationStore, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store.to_dict(), fh, indent=2)


def annotate_update(store: AnnotationStore, project: str, package: str, note: str, author: str = "depwatch") -> Annotation:
    ann = Annotation(project=project, package=package, note=note, author=author)
    store.add(ann)
    return ann
