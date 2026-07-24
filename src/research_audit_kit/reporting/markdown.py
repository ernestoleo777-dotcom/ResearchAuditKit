"""Small deterministic Markdown rendering helpers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: Iterable[Mapping[str, Any]], columns: Sequence[str]) -> str:
    materialized = list(rows)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    lines.extend(
        "| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |"
        for row in materialized
    )
    return "\n".join(lines)

