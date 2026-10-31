# SPDX-License-Identifier: Apache-2.0
"""Replay synthetic CLI cases in temporary copies; do not alter shipped fixtures."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


def replay():
    source = Path(__file__).resolve().parent
    summaries = []
    with TemporaryDirectory(prefix="rak-evidence-demo-") as temporary:
        base = Path(temporary).resolve()
        cases = [
            ("validate", "validate", 0, "PASS", None),
            ("matched", "doctor", 2, "UNRESOLVED", "MECHANICALLY_VERIFIED"),
            ("changed", "doctor", 1, "INVALID", "IDENTITY_MISMATCH"),
            ("missing", "doctor", 2, "UNRESOLVED", "MISSING"),
        ]
        for name, command, expected_exit, expected_status, expected_artifact in cases:
            target = base / name
            target.mkdir()
            for filename in ("graph.json", "artifact.txt"):
                shutil.copyfile(source / filename, target / filename)
            if name == "changed":
                (target / "artifact.txt").write_text("Changed synthetic bytes.\n", encoding="utf-8")
            elif name == "missing":
                (target / "artifact.txt").unlink()
            completed = subprocess.run(
                [sys.executable, "-m", "research_audit_kit", "evidence", command,
                 str(target / "graph.json")], capture_output=True, text=True, check=False,
                timeout=30,
            )
            result = json.loads(completed.stdout)
            observations = result["artifact_observations"]
            actual_artifact = observations[0]["status"] if observations else None
            actual = (completed.returncode, result["status"], actual_artifact)
            expected = (expected_exit, expected_status, expected_artifact)
            if actual != expected:
                raise RuntimeError(f"{name}: expected {expected}, got {actual}")
            summaries.append({"case": name, "exit_code": completed.returncode,
                              "status": result["status"], "artifact_status": actual_artifact,
                              "scientific_adjudication": result["scope_limits"]["scientific_adjudication"]})
    return summaries


if __name__ == "__main__":
    print(json.dumps(replay(), indent=2, sort_keys=True))
