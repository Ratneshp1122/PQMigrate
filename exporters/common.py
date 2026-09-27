"""Shared normalization helpers for external exports."""

import os
from pathlib import Path
from typing import Any, Iterable


def records(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list(report.get("records") or [])


def source_root(report: dict[str, Any]) -> Path | None:
    paths = [
        Path(record["finding"]["location"]["file_path"]).resolve()
        for record in records(report)
        if record.get("finding", {}).get("location", {}).get("file_path")
    ]
    if not paths:
        return None
    try:
        common = Path(os.path.commonpath([str(path) for path in paths]))
    except ValueError:
        return None
    return common.parent if common.is_file() or common.suffix else common


def relative_path(file_path: str, root: Path | None) -> str:
    path = Path(file_path).resolve()
    if root is not None:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            pass
    return path.name


def joined(values: Iterable[Any] | None) -> str:
    return ", ".join(str(value) for value in (values or []))


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
