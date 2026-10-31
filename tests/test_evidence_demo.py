from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_public_demo_exercises_cli_without_mutating_shipped_fixtures():
    directory = ROOT / "examples/evidence_graph_demo"
    before = {name: (directory / name).read_bytes()
              for name in ("graph.json", "artifact.txt")}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run([sys.executable, str(directory / "run_demo.py")],
                               cwd=ROOT, env=env, capture_output=True, text=True,
                               check=False, timeout=120)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    rows = json.loads(completed.stdout)
    assert [(row["case"], row["exit_code"], row["artifact_status"]) for row in rows] == [
        ("validate", 0, None), ("matched", 2, "MECHANICALLY_VERIFIED"),
        ("changed", 1, "IDENTITY_MISMATCH"), ("missing", 2, "MISSING"),
        ("impact-changed", 1, "IDENTITY_MISMATCH"), ("impact-missing", 2, "MISSING"),
    ]
    for row in rows[-2:]:
        assert row["potentially_affected_claim_ids"] == ["urn:rak:demo:claim:statement@1"]
        assert row["claim_paths"][0]["node_ids"] == [
            "urn:rak:demo:artifact:record@1", "urn:rak:demo:evidence:observation@1",
            "urn:rak:demo:claim:statement@1",
        ]
    assert all(row["scientific_adjudication"] == "NOT_PERFORMED" for row in rows)
    assert {name: (directory / name).read_bytes() for name in before} == before
