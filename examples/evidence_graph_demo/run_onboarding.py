# SPDX-License-Identifier: Apache-2.0
"""Run the asset-list-to-readable-impact workflow in an isolated synthetic copy."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


def replay():
    source = Path(__file__).resolve().parent
    with TemporaryDirectory(prefix="rak-onboarding-") as temporary:
        root = Path(temporary).resolve()
        for filename in ("assets.json", "artifact.txt"):
            shutil.copyfile(source / filename, root / filename)
        initialized = subprocess.run(
            [sys.executable, "-m", "research_audit_kit", "evidence", "init", "--manifest",
             str(root / "assets.json"), "--out", "graph.json", "--namespace", "demo"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if initialized.returncode != 0:
            raise RuntimeError(initialized.stdout + initialized.stderr)
        (root / "artifact.txt").write_bytes(b"Intentional synthetic change.\n")
        impacted = subprocess.run(
            [sys.executable, "-m", "research_audit_kit", "evidence", "impact",
             str(root / "graph.json"), "--format", "human", "--out", "impact.json"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if impacted.returncode != 1:
            raise RuntimeError(impacted.stdout + impacted.stderr)
        report = json.loads((root / "impact.json").read_text())
        if report["impact_analysis"]["potentially_affected_claim_ids"] != ["urn:rak:demo:claim:statement@1"]:
            raise RuntimeError("The declared claim was not reached")
        print(initialized.stdout.rstrip())
        print()
        print(impacted.stdout.rstrip())


if __name__ == "__main__":
    replay()
