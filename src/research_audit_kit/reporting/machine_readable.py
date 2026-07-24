"""Machine-readable summary writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..io.json_io import write_json
from ..io.yaml_io import write_yaml


def write_machine_summary(
    out_dir: str | Path, summary: Mapping[str, Any], *, prefix: str = "summary"
) -> dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    return {
        "json": write_json(target / f"{prefix}.json", dict(summary)),
        "yaml": write_yaml(target / f"{prefix}.yaml", dict(summary)),
    }

