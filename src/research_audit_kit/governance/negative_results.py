# SPDX-License-Identifier: Apache-2.0
"""Preserve failed outcomes in YAML, CSV, and Markdown."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from ..io.csv_io import write_csv_rows
from ..io.yaml_io import write_yaml


def preserve_negative_results(
    results: Iterable[Mapping[str, Any]], out_dir: str | Path
) -> dict[str, Path]:
    rows = [dict(row) for row in results]
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    yaml_path = write_yaml(target / "negative_results.yaml", {"results": rows})
    fieldnames = sorted({str(key) for row in rows for key in row}) or ["status"]
    csv_path = write_csv_rows(target / "negative_results.csv", rows, fieldnames)
    markdown_path = target / "negative_results.md"
    lines = ["# Negative Results", "", "A FAIL is an adjudicated outcome, not automatically a software defect.", ""]
    for row in rows:
        lines.append(f"- `{row.get('id', 'unnamed')}`: `{row.get('status', 'UNADJUDICATED')}` — {row.get('interpretation', '')}")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"yaml": yaml_path, "csv": csv_path, "markdown": markdown_path}

