"""Export dependency update reports to JSON and Markdown formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from depwatch.reporter import Report


def export_json(report: Report, path: Union[str, Path]) -> None:
    """Write the report as a JSON file."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2)


def export_markdown(report: Report, path: Union[str, Path]) -> None:
    """Write the report as a Markdown file."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# depwatch update report\n"]

    if report.is_empty():
        lines.append("_No updates found._\n")
    else:
        for entry in report.entries:
            lines.append(f"## {entry.project_name}\n")
            for update in entry.updates:
                lines.append(
                    f"- **{update.package_name}**: "
                    f"{update.current_version} → {update.latest_version}\n"
                )
            lines.append("")

    with dest.open("w", encoding="utf-8") as fh:
        fh.writelines(lines)


def export_report(
    report: Report,
    fmt: str,
    path: Union[str, Path],
) -> None:
    """Dispatch to the appropriate exporter based on *fmt*.

    Supported formats: ``json``, ``markdown`` / ``md``.
    """
    fmt = fmt.lower().strip()
    if fmt == "json":
        export_json(report, path)
    elif fmt in ("markdown", "md"):
        export_markdown(report, path)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")
