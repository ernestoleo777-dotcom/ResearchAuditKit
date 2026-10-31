# SPDX-License-Identifier: Apache-2.0
"""Readable projections of canonical results; no extra reads or adjudication."""
from __future__ import annotations

import json
import unicodedata

MAX_LINES = 400
MAX_LINE_CHARS = 2000


def display(value) -> str:
    value = str(value)
    if len(value) > 512:
        value = value[:512] + " [truncated; see JSON]"
    escaped = json.dumps(value, ensure_ascii=False)[1:-1]
    return "".join(json.dumps(char, ensure_ascii=True)[1:-1]
                   if unicodedata.category(char) in {"Cf", "Cs", "Zl", "Zp"}
                   else char for char in escaped)


def _review(status):
    if status == "IDENTITY_MISMATCH":
        return "Review the byte change and declared version before changing the recorded identity."
    if status == "MISSING":
        return "Confirm the listed location and availability, then rerun the check."
    if "BUDGET" in status:
        return "Review the explicit read budget; the file identity remains unresolved."
    return "Review availability, access and identity metadata, then rerun the check."


def render_human(result: dict) -> str:
    lines = []
    clipped = False

    def add(value=""):
        nonlocal clipped
        if len(lines) >= MAX_LINES:
            clipped = True
            return
        if len(value) > MAX_LINE_CHARS:
            value = value[:MAX_LINE_CHARS] + " [line truncated; see JSON]"
        lines.append(value)

    command = result.get("command", "unknown")
    add(f"ResearchAuditKit evidence {display(command)}")
    add(f"Result: {display(result.get('status', 'UNRESOLVED'))}")
    observations = result.get("artifact_observations", [])
    if command == "init":
        created = result.get("output_created", False)
        add(f"Graph: {display(result.get('output_path') or '(none)')} ({'created' if created else 'not created'})")
        counts = result.get("generated_node_counts", {})
        add(f"Generated: Artifact={counts.get('Artifact', 0)} Evidence={counts.get('Evidence', 0)} Claim={counts.get('Claim', 0)}")
        add("Captured hashes describe current bytes only; claims remain UNRESOLVED.")
        for observation in observations:
            add(f"Asset: {display(observation['path'])} [{display(observation['status'])}]")
        add("Review items: Check your listed assets, statements and explicit support/contradiction links.")
        if created:
            add("Next: run evidence doctor or evidence impact on the generated graph.")
    elif command == "impact":
        analysis = result["impact_analysis"]
        add(f"Impact analysis: {display(analysis['analysis_status'])}")
        add(f"Problem files: {len(analysis['artifacts'])}; claims reached: {len(analysis['potentially_affected_claim_ids'])}")
        if analysis["analysis_status"] != "COMPLETE":
            add("Review items: Analysis is not complete; do not treat omitted paths as unaffected.")
        for reason in analysis["incomplete_reasons"]:
            add(f"Analysis limit: {display(reason)}")
        nodes = {node["id"]: node for node in result.get("nodes_visited", [])}
        for artifact in analysis["artifacts"]:
            add()
            add(f"Problem file: {display(artifact['path'])} [{display(artifact['observation_status'])}]")
            change = "confirmed stable-byte mismatch" if artifact["identity_change"] == "CONFIRMED" else "identity unresolved"
            add(f"Identity: {change}")
            for claim_id in artifact["potentially_affected_claim_ids"]:
                add(f"Claim to review: {display(claim_id)}")
                if "statement" in nodes.get(claim_id, {}):
                    add(f"  Statement: {display(nodes[claim_id]['statement'])}")
            if not artifact["potentially_affected_claim_ids"]:
                add("Claims to review: none reached in the examined declared relationships.")
            for path in artifact["claim_paths"]:
                chain = display(path["node_ids"][0])
                for relation, node_id in zip(path["relations"], path["node_ids"][1:]):
                    chain += f" --{display(relation)}--> {display(node_id)}"
                add(f"Declared path ({path['citation_context']}; {path['claim_version_state']}): {chain}")
            add(f"Review items: {_review(artifact['observation_status'])}")
        if not analysis["artifacts"] and analysis["analysis_status"] == "COMPLETE":
            add("No artifact identity issues observed within the declared scope.")
        add(f"Not reached: {len(analysis['not_reached_claim_ids'])} claim(s); this does not establish they are unaffected.")
    else:
        add(f"Nodes: {len(result.get('nodes_visited', []))}; observed artifacts: {len(observations)}")
        if command == "validate":
            add("Scope: structure only; artifact contents were not read.")
        for observation in observations:
            add(f"File: {display(observation['path'])} [{display(observation['status'])}]")
        add("Review items: Inspect unresolved declarations and any reported identity or reference issues.")
    findings = result.get("findings", [])
    add()
    add(f"Findings: {len(findings)}")
    for item in findings[:20]:
        add(f"- {display(item['severity'])}: {display(item['code'])} {display(item['node_id'] or item['path'])}".rstrip())
    if len(findings) > 20:
        add(f"{len(findings) - 20} more finding(s); use --format json for full details.")
    if clipped:
        lines.append("Text report truncated at 400 lines; use --format json for full details.")
    lines.append("Boundary: declared relationships and current-byte observations only; no scientific adjudication.")
    return "\n".join(lines)
