# SPDX-License-Identifier: Apache-2.0
"""Unified, zero-configuration repository release audit."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..exceptions import AuditError, UnsafePathError
from .inventory import build_inventory
from .policy import IntegrityPolicy

AUDIT_SCHEMA_VERSION = "researchauditkit.audit/v1"

FINDING_PASS = "PASS"
FINDING_WARNING = "WARNING"
FINDING_RELEASE_BLOCKER = "RELEASE_BLOCKER"
FINDING_NOT_APPLICABLE = "NOT_APPLICABLE"
FINDING_UNRESOLVED = "UNRESOLVED"

FINDING_STATUSES = (
    FINDING_PASS,
    FINDING_WARNING,
    FINDING_RELEASE_BLOCKER,
    FINDING_NOT_APPLICABLE,
    FINDING_UNRESOLVED,
)

RESULT_PASS = "PASS"
RESULT_WARNING = "WARNING"
RESULT_RELEASE_BLOCKER = "RELEASE_BLOCKER"
RESULT_ABSTAIN = "ABSTAIN"

BUILT_IN_POLICY_ID = "rak-generic-release-v1"

_README_CANDIDATES = frozenset({"readme", "readme.md", "readme.rst", "readme.txt"})
_LICENSE_CANDIDATES = frozenset(
    {
        "copying",
        "copying.md",
        "copying.txt",
        "license",
        "license.md",
        "license.rst",
        "license.txt",
    }
)
_DIGEST_FIELDS = (
    "path",
    "size_bytes",
    "sha256",
    "category",
    "gate_status",
    "exclusion_reason",
)


def built_in_audit_policy() -> IntegrityPolicy:
    """Return the conservative, generic release-audit policy."""

    return IntegrityPolicy.from_dict(
        {
            "policy": {
                "id": BUILT_IN_POLICY_ID,
                "include_patterns": ["**/*"],
                "exclude_patterns": [
                    ".pytest_cache/**",
                    ".ruff_cache/**",
                    ".mypy_cache/**",
                    ".venv/**",
                    "venv/**",
                    "**/__pycache__/**",
                    "**/*.pyc",
                    "**/*.pyo",
                ],
                "volatile_patterns": [".DS_Store", "**/.DS_Store"],
                "required_files": [],
                "unexpected_scientific_file_policy": "warn",
                "metadata": {
                    "purpose": "generic-public-ml-research-release-audit",
                    "version": 1,
                },
            }
        }
    )


def _finding(check_id: str, status: str, message: str, location: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "location": location,
        "message": message,
        "status": status,
    }


def _safe_location(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return "<external-policy>"


def _safe_message(exc: BaseException, root: Path, policy_path: Path | None = None) -> str:
    message = str(exc).replace(str(root), ".")
    if policy_path is not None:
        message = message.replace(str(policy_path), _safe_location(policy_path, root))
    return message


def _inventory_digest(rows: Iterable[dict[str, object]]) -> str:
    normalized = [
        {field: row[field] for field in _DIGEST_FIELDS}
        for row in sorted(rows, key=lambda item: str(item["path"]))
    ]
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _overall_status(findings: Iterable[dict[str, str]]) -> str:
    statuses = {finding["status"] for finding in findings}
    if FINDING_RELEASE_BLOCKER in statuses:
        return RESULT_RELEASE_BLOCKER
    if FINDING_UNRESOLVED in statuses:
        return RESULT_ABSTAIN
    if FINDING_WARNING in statuses:
        return RESULT_WARNING
    return RESULT_PASS


def _result(
    *,
    root_identifier: str,
    policy: dict[str, object],
    findings: list[dict[str, str]],
    asset_count: int,
    inventory_sha256: str | None,
) -> dict[str, Any]:
    ordered = sorted(
        findings,
        key=lambda finding: (
            finding["check_id"],
            finding["location"],
            finding["status"],
            finding["message"],
        ),
    )
    raw_counts = Counter(finding["status"] for finding in ordered)
    counts = {status: raw_counts.get(status, 0) for status in FINDING_STATUSES}
    return {
        "command": "audit",
        "counts": counts,
        "findings": ordered,
        "inventory": {
            "asset_count": asset_count,
            "content_sha256": inventory_sha256,
        },
        "limitations": [
            "Results are mechanical observations over local files and declared policy.",
            "PASS is not scientific correctness, reproducibility certification, or peer review.",
            "The audit does not execute target repository code or use a network service.",
        ],
        "policy": policy,
        "schema_version": AUDIT_SCHEMA_VERSION,
        "status": _overall_status(ordered),
        "target": {"root_identifier": root_identifier},
    }


def audit_repository(
    root: str | Path = ".",
    *,
    policy_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Audit universally observable repository release mechanics.

    A project policy replaces the built-in inventory classification and required-file
    declarations. Universal path-safety, README/license presence, symlink reporting,
    deterministic inventory, and non-certification boundaries still apply.
    """

    requested_root = Path(root)
    base = requested_root.resolve()
    root_identifier = base.name or "."
    findings: list[dict[str, str]] = []

    if not base.is_dir():
        findings.append(
            _finding(
                "repository.readable",
                FINDING_UNRESOLVED,
                "Target is not a readable directory.",
                ".",
            )
        )
        return _result(
            root_identifier=root_identifier,
            policy={
                "available": False,
                "mode": "unresolved",
                "path": None,
                "policy_id": None,
            },
            findings=findings,
            asset_count=0,
            inventory_sha256=None,
        )

    explicit_policy = policy_path is not None
    candidate = Path(policy_path).resolve() if explicit_policy else base / ".rak" / "policy.yaml"
    policy_available = candidate.is_file()
    policy_location = _safe_location(candidate, base) if policy_available or explicit_policy else None

    if explicit_policy and not policy_available:
        findings.append(
            _finding(
                "policy.configuration",
                FINDING_UNRESOLVED,
                "Explicit policy file does not exist.",
                policy_location or "<external-policy>",
            )
        )
        return _result(
            root_identifier=root_identifier,
            policy={
                "available": False,
                "mode": "unresolved",
                "path": policy_location,
                "policy_id": None,
            },
            findings=findings,
            asset_count=0,
            inventory_sha256=None,
        )

    if policy_available:
        try:
            policy = IntegrityPolicy.from_yaml(candidate)
        except (AuditError, OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            findings.append(
                _finding(
                    "policy.configuration",
                    FINDING_UNRESOLVED,
                    f"Project policy could not be applied: {_safe_message(exc, base, candidate)}",
                    policy_location or "<external-policy>",
                )
            )
            return _result(
                root_identifier=root_identifier,
                policy={
                    "available": True,
                    "mode": "unresolved",
                    "path": policy_location,
                    "policy_id": None,
                },
                findings=findings,
                asset_count=0,
                inventory_sha256=None,
            )
        policy_mode = "project"
        findings.append(
            _finding(
                "policy.configuration",
                FINDING_PASS,
                f"Applied declared project policy {policy.policy_id!r}.",
                policy_location or "<external-policy>",
            )
        )
    else:
        policy = built_in_audit_policy()
        policy_mode = "built-in"
        findings.append(
            _finding(
                "policy.configuration",
                FINDING_NOT_APPLICABLE,
                "No .rak/policy.yaml was found; applied the built-in generic policy.",
                ".rak/policy.yaml",
            )
        )

    omitted = {".git"}
    if output_path is not None:
        output = Path(output_path).resolve()
        try:
            omitted.add(output.relative_to(base).as_posix())
        except ValueError:
            pass

    try:
        rows = build_inventory(base, policy, omit_paths=sorted(omitted))
    except UnsafePathError as exc:
        findings.append(
            _finding(
                "repository.path-safety",
                FINDING_RELEASE_BLOCKER,
                _safe_message(exc, base, candidate if policy_available else None),
                ".",
            )
        )
        return _result(
            root_identifier=root_identifier,
            policy={
                "available": policy_available,
                "mode": policy_mode,
                "path": policy_location,
                "policy_id": policy.policy_id,
            },
            findings=findings,
            asset_count=0,
            inventory_sha256=None,
        )
    except (AuditError, OSError, UnicodeError, ValueError) as exc:
        findings.append(
            _finding(
                "repository.inventory",
                FINDING_UNRESOLVED,
                f"Inventory could not be completed: {_safe_message(exc, base)}",
                ".",
            )
        )
        return _result(
            root_identifier=root_identifier,
            policy={
                "available": policy_available,
                "mode": policy_mode,
                "path": policy_location,
                "policy_id": policy.policy_id,
            },
            findings=findings,
            asset_count=0,
            inventory_sha256=None,
        )

    findings.extend(
        [
            _finding(
                "repository.inventory",
                FINDING_PASS,
                f"Inventoried {len(rows)} files in deterministic path order.",
                ".",
            ),
            _finding(
                "repository.path-safety",
                FINDING_PASS,
                "All inventoried paths remained within the target root.",
                ".",
            ),
            _finding(
                "repository.readable",
                FINDING_PASS,
                "Target directory was readable without executing repository code.",
                ".",
            ),
        ]
    )

    root_names = {
        str(row["path"]).casefold()
        for row in rows
        if "/" not in str(row["path"]) and row["gate_status"] != "MISSING_REQUIRED"
    }
    if root_names & _README_CANDIDATES:
        findings.append(
            _finding("repository.readme", FINDING_PASS, "Repository-root README found.", "README")
        )
    else:
        findings.append(
            _finding(
                "repository.readme",
                FINDING_WARNING,
                "No repository-root README was found.",
                "README",
            )
        )

    if root_names & _LICENSE_CANDIDATES:
        findings.append(
            _finding("repository.license", FINDING_PASS, "Repository-root license found.", "LICENSE")
        )
    else:
        findings.append(
            _finding(
                "repository.license",
                FINDING_WARNING,
                "No repository-root license file was found.",
                "LICENSE",
            )
        )

    symlinks = [row for row in rows if row["exclusion_reason"] == "symlink recorded but target was not followed"]
    if symlinks:
        findings.extend(
            _finding(
                "repository.symlink",
                FINDING_WARNING,
                "In-root symlink was recorded but its target was not followed.",
                str(row["path"]),
            )
            for row in symlinks
        )
    else:
        findings.append(
            _finding(
                "repository.symlink",
                FINDING_PASS,
                "No symlinks were observed in the inventoried paths.",
                ".",
            )
        )

    missing = [row for row in rows if row["gate_status"] == "MISSING_REQUIRED"]
    if missing:
        findings.extend(
            _finding(
                "policy.required-file",
                FINDING_RELEASE_BLOCKER,
                "A file required by the declared policy is missing.",
                str(row["path"]),
            )
            for row in missing
        )
    elif policy.required_files:
        findings.append(
            _finding(
                "policy.required-files",
                FINDING_PASS,
                f"All {len(policy.required_files)} policy-required files were present.",
                policy_location or ".rak/policy.yaml",
            )
        )
    else:
        findings.append(
            _finding(
                "policy.required-files",
                FINDING_NOT_APPLICABLE,
                "The active policy declares no required files.",
                policy_location or ".rak/policy.yaml",
            )
        )

    return _result(
        root_identifier=root_identifier,
        policy={
            "available": policy_available,
            "mode": policy_mode,
            "path": policy_location,
            "policy_id": policy.policy_id,
        },
        findings=findings,
        asset_count=len(rows),
        inventory_sha256=_inventory_digest(rows),
    )


def format_audit_human(result: dict[str, Any]) -> str:
    """Render a concise, deterministic terminal summary."""

    counts = result["counts"]
    policy = result["policy"]
    lines = [
        "ResearchAuditKit audit",
        f"Target: {result['target']['root_identifier']}",
        f"Policy: {policy['mode']} ({policy['policy_id'] or 'unresolved'})",
        f"Result: {result['status']}",
        (
            "Findings: "
            + " ".join(f"{status}={counts[status]}" for status in FINDING_STATUSES)
        ),
    ]
    actionable = [
        finding
        for finding in result["findings"]
        if finding["status"] in {FINDING_WARNING, FINDING_RELEASE_BLOCKER, FINDING_UNRESOLVED}
    ]
    if actionable:
        lines.extend(
            f"- {finding['status']} {finding['check_id']} [{finding['location']}]: {finding['message']}"
            for finding in actionable
        )
    else:
        lines.append("- No warnings, unresolved checks, or release blockers.")
    lines.append(
        "Boundary: PASS is mechanical only; it is not scientific correctness or certification."
    )
    return "\n".join(lines)


def audit_exit_code(result: dict[str, Any], *, fail_on: str) -> int:
    """Map the audit result to the established 0/2 CLI contract."""

    if result["status"] in {RESULT_RELEASE_BLOCKER, RESULT_ABSTAIN}:
        return 2
    if fail_on == "warning" and result["status"] == RESULT_WARNING:
        return 2
    return 0
