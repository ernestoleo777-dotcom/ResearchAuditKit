#!/usr/bin/env python3
"""Render a ResearchAuditKit audit result for GitHub Job Summary."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import sys
from typing import Any


def _cell(value: object) -> str:
    return escape(str(value).replace("\r", " ").replace("\n", " ")).replace("|", "&#124;")


def render(result: dict[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "## ResearchAuditKit audit",
        "",
        f"**Status:** `{_cell(result['status'])}`  ",
        f"**Target:** `{_cell(result['target']['root_identifier'])}`  ",
        f"**Policy:** `{_cell(result['policy']['mode'])}` / `{_cell(result['policy']['policy_id'])}`  ",
        f"**Schema:** `{_cell(result['schema_version'])}`",
        "",
        (
            "Findings: "
            f"PASS={counts['PASS']}, WARNING={counts['WARNING']}, "
            f"RELEASE_BLOCKER={counts['RELEASE_BLOCKER']}, "
            f"NOT_APPLICABLE={counts['NOT_APPLICABLE']}, UNRESOLVED={counts['UNRESOLVED']}."
        ),
    ]
    actionable = [finding for finding in result["findings"] if finding["status"] != "PASS"]
    if actionable:
        lines.extend(
            [
                "",
                "| Status | Check | Location | Finding |",
                "| --- | --- | --- | --- |",
                *[
                    "| "
                    + " | ".join(
                        _cell(finding[key])
                        for key in ("status", "check_id", "location", "message")
                    )
                    + " |"
                    for finding in actionable
                ],
            ]
        )
    lines.extend(
        [
            "",
            "> Mechanical release checks only. This is not scientific correctness, "
            "reproducibility certification, or peer review.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: render-summary.py RESULT.json", file=sys.stderr)
        return 2
    result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
