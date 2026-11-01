# SPDX-License-Identifier: Apache-2.0
"""Explicit interactive asset-list authoring; no discovery or asset reads."""
from __future__ import annotations

import json
from pathlib import Path
import os
import sys

from .core import Limits, finding, finish
from .fs import EvidenceError, Root, no_download
from .initialize import ASSET_LIST_SCHEMA, scaffold


def wizard(*, root=".", output="assets.json", ask=None, show=None):
    if show is None:
        show = lambda message: print(message, file=sys.stderr)
    if ask is None:
        def ask(message):
            print(message, end="", file=sys.stderr, flush=True)
            return input()
    result = dict(schema="researchauditkit.evidence-wizard/v1", command="wizard",
                  findings=[], output_created=False, output_path=None,
                  asset_contents_read=False, relationships="USER_SUPPLIED_ONLY")
    handle = None
    def prompt(message):
        value = ask(message).strip()
        if len(value) > 65536:
            raise EvidenceError("INPUT_TOO_LONG")
        return value
    try:
        manifest = dict(schema=ASSET_LIST_SCHEMA, assets=[], claims=[])
        show("List explicit project-relative paths. No directory scan or file contents will be read.")
        show("Names use letters, digits, dots, underscores or hyphens. Blank name ends each section.")
        while True:
            name = prompt("Asset name (blank to finish): ")
            if not name:
                break
            manifest["assets"].append(dict(name=name, path=prompt("Relative file path: ")))
            if len(manifest["assets"]) > Limits().nodes // 2:
                raise EvidenceError("GRAPH_SIZE_BUDGET_EXCEEDED")
        while True:
            name = prompt("Claim name (optional; blank to finish): ")
            if not name:
                break
            manifest["claims"].append(dict(
                name=name, statement=prompt("Your claim statement: "),
                supports=[v.strip() for v in prompt("Supporting asset names (comma-separated, or blank): ").split(",") if v.strip()],
                contradicts=[v.strip() for v in prompt("Contradicting asset names (comma-separated, or blank): ").split(",") if v.strip()],
            ))
            if len(manifest["claims"]) > Limits().nodes:
                raise EvidenceError("GRAPH_SIZE_BUDGET_EXCEEDED")
        scaffold(manifest, "project", "1", Limits())
        if len(json.dumps(manifest).encode()) > Limits().graph_bytes:
            raise EvidenceError("MANIFEST_BUDGET_EXCEEDED")
        show("Preview (declarations only; claims remain unresolved):")
        show(json.dumps(manifest, indent=2, ensure_ascii=True))
        if prompt("Create this asset list? Type yes: ").lower() != "yes":
            raise EvidenceError("USER_CANCELLED", "UNRESOLVED")
        with no_download():
            handle = Root(Path(os.path.abspath(root)))
            relative = handle.output_relative(output, {a["path"] for a in manifest["assets"]})
        handle.publish(relative, manifest)
        result.update(output_created=True, output_path=relative)
    except (EOFError, KeyboardInterrupt):
        result["findings"].append(finding("USER_CANCELLED"))
    except EvidenceError as exc:
        result["findings"].append(finding(exc.code, exc.severity))
    except (OSError, UnicodeError):
        result["findings"].append(finding("LOCAL_IO_UNAVAILABLE"))
    finally:
        if handle is not None:
            handle.close()
    return finish(result)
