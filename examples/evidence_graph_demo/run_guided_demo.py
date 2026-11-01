# SPDX-License-Identifier: Apache-2.0
"""Replay RC4's real CLI in a temporary synthetic project; preserve shipped files."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def replay():
    with TemporaryDirectory(prefix="rak-guided-demo-") as temporary:
        root = Path(temporary).resolve()
        artifact = root / "results.csv"
        artifact.write_bytes(b"metric,value\naccuracy,0.8\n")
        def invoke(arguments, expected=0, data=None):
            done = subprocess.run([sys.executable, "-m", "research_audit_kit", "evidence", *arguments],
                                  input=data, text=True, capture_output=True, timeout=30)
            if done.returncode != expected:
                raise RuntimeError(done.stdout + done.stderr)
            return done.stdout
        invoke(["wizard", "--root", str(root), "--format", "json"],
               data="results\nresults.csv\n\nmain\nAn explicitly declared example claim\nresults\n\n\nyes\n")
        receipt = json.loads(invoke(["init", "--manifest", str(root / "assets.json"),
                                     "--out", "graph.json", "--format", "json"]))
        command = ["check", str(root / "graph.json"), "--graph-sha256", receipt["graph_content_sha256"],
                   "--allow-unresolved-claim", "urn:rak:project:claim:main@1", "--format", "markdown"]
        matched = invoke(command)
        assert "Mechanical gate: **PASS**" in matched
        artifact.write_bytes(b"metric,value\naccuracy,0.7\n")
        changed = invoke(command, expected=1)
        assert "Declared path:" in changed and "Mechanical gate: **FAIL**" in changed
        print("Synthetic replay: baseline matches, then controlled file change.\n")
        print(matched)
        print(changed)


if __name__ == "__main__":
    replay()
