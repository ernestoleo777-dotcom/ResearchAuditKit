# SPDX-License-Identifier: Apache-2.0
"""Machine-readable support-audit reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from ..io.csv_io import read_csv_rows, write_csv_rows
from ..io.json_io import write_json
from .joint import cartesian_gap, observed_combination_table
from .marginal import marginal_support
from .missingness import classify_missingness


def support_audit_report(
    data_path: str | Path,
    features: Sequence[str],
    *,
    discrete: Sequence[str] = (),
    schema: Mapping[str, Any] | None = None,
    out_dir: str | Path,
) -> dict[str, Any]:
    rows = read_csv_rows(data_path)
    missing_columns = [feature for feature in features if rows and feature not in rows[0]]
    if missing_columns:
        raise ValueError(f"missing feature columns: {missing_columns}")
    summary: dict[str, Any] = {
        "row_count": len(rows),
        "features": list(features),
        "marginal_support": marginal_support(rows, features),
        "joint_support_size": len(observed_combination_table(rows, features)),
        "claim_boundary": "Empirical support only; no physical interpretation is produced.",
    }
    if set(features) <= set(discrete):
        summary["cartesian_gap"] = cartesian_gap(rows, features, discrete=discrete)
        summary["missingness"] = classify_missingness(
            rows, features, discrete=discrete, schema=schema
        )
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    combinations = observed_combination_table(rows, features)
    write_csv_rows(target / "observed_combinations.csv", combinations, [*features, "frequency"])
    write_json(target / "support_summary.json", summary)
    return summary

