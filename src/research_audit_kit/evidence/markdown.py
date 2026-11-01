# SPDX-License-Identifier: Apache-2.0
"""Bounded, inert GitHub Markdown projection of canonical evidence results."""
from __future__ import annotations

import html

from .human import display


def cell(value):
    value = html.escape(display(value), quote=True)
    for char in "`|[]*_~\\":
        value = value.replace(char, f"&#{ord(char)};")
    return value


def render_markdown(result):
    lines = ["## ResearchAuditKit evidence report", ""]
    report = result
    if result["command"] == "check":
        lines += [f"Mechanical gate: **{cell(result['mechanical_gate'])}**",
                  f"Evidence status: **{cell(result['evidence_status'])}**", ""]
        report = result["evidence_result"]
    else:
        lines += [f"Operation: {cell(result['command'])}; status: **{cell(result['status'])}**", ""]
    if result["command"] in ("init", "wizard"):
        lines += [f"Output created: {cell(result['output_created'])}",
                  f"Output path: {cell(result.get('output_path') or '(none)')}", ""]
        if result.get("graph_content_sha256"):
            lines += [f"Graph content SHA-256: `{result['graph_content_sha256']}`", ""]
    observations = report.get("artifact_observations", [])
    lines += ["### File observations", "", "| File | Status |", "| --- | --- |"]
    for row in observations:
        lines.append(f"| {cell(row['path'])} | {cell(row['status'])} |")
    if not observations:
        lines.append("| No artifact observations | See operation scope and findings |")
    analysis = report.get("impact_analysis")
    if analysis:
        lines += ["", f"Impact analysis: **{cell(analysis['analysis_status'])}**", "",
                  "### Claims to review", ""]
        nodes = {node["id"]: node for node in report.get("nodes_visited", [])}
        for artifact in analysis["artifacts"]:
            lines.append(f"- Problem file: {cell(artifact['path'])}")
            for path in artifact["claim_paths"]:
                lines.append(f"  - Claim: {cell(path['claim_id'])} ({cell(path['citation_context'])})")
                if nodes.get(path["claim_id"], {}).get("statement"):
                    lines.append(f"  - Statement: {cell(nodes[path['claim_id']]['statement'])}")
                chain = cell(path["node_ids"][0])
                for relation, identity in zip(path["relations"], path["node_ids"][1:]):
                    chain += f" → {cell(relation)} → {cell(identity)}"
                lines.append(f"  - Declared path: {chain}")
        lines += ["", "Review file availability, byte changes and declared versions before updating a baseline.",
                  "Omitted or unreached claims are not certified unaffected."]
    lines += ["", "### Findings", ""]
    for row in result["findings"][:20]:
        lines.append(f"- {cell(row['severity'])}: {cell(row['code'])} {cell(row['node_id'] or row['path'])}")
    if len(result["findings"]) > 20:
        lines.append("Further findings omitted; see canonical JSON.")
    if not result["findings"]:
        lines.append("No blocking findings; accepted unresolved declarations remain unchanged.")
    if len(lines) > 390:
        lines = lines[:390] + ["", "Report truncated; see canonical JSON for complete details."]
    lines = [line[:2000] + " [line truncated; see JSON]" if len(line) > 2000 else line for line in lines]
    lines += ["", "**Boundary:** current-byte observations and user-declared relationships only. "
              "No scientific adjudication; observations are not an atomic multi-file snapshot."]
    return "\n".join(lines) + "\n"
