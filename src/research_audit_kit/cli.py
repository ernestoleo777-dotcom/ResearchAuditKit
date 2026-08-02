# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for ResearchAuditKit."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .constants import (
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_UNADJUDICATED,
    __version__,
)
from .exceptions import AuditError, InputValidationError
from .governance.claims import CLAIM_FIELDS, evaluate_claims
from .governance.deviations import record_deviation
from .governance.evidence_index import build_evidence_index, write_evidence_index
from .governance.gates import evaluate_gate
from .integrity.baseline import freeze_baseline
from .integrity.inventory import build_inventory, write_inventory
from .integrity.isolation import audit_isolation, write_isolation_audit
from .integrity.policy import IntegrityPolicy
from .integrity.prediction_seal import (
    seal_prediction_declaration,
    verify_prediction_seal,
    write_prediction_seal,
)
from .integrity.verification import verify_baseline, write_verification
from .io.csv_io import read_csv_rows, write_csv_rows
from .io.json_io import read_json, read_json_strict, write_json
from .io.yaml_io import read_yaml
from .optimization_audit.contamination import contamination_metrics
from .optimization_audit.pareto import validate_pareto_claims
from .reporting.machine_readable import write_machine_summary
from .support.report import support_audit_report
from .validation.leakage import audit_split_leakage


def _csv_list(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _objectives(value: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for item in _csv_list(value):
        try:
            name, direction = item.rsplit(":", 1)
        except ValueError as exc:
            raise InputValidationError("objectives must use name:min or name:max") from exc
        result.append((name, direction))
    return result


def _print_summary(summary: dict[str, Any]) -> None:
    print(json.dumps(summary, sort_keys=True))


def _output_omit_paths(root: str | Path, output: str | Path) -> list[str]:
    try:
        relative = Path(output).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return []
    return [relative]


def _run(args: argparse.Namespace) -> int:
    if args.command == "init":
        root = Path(args.root)
        policy = IntegrityPolicy.from_yaml(args.policy)
        state_dir = root / ".rak"
        if state_dir.exists():
            raise AuditError(f"already initialized: {state_dir}")
        state_dir.mkdir(parents=True)
        summary = {"command": "init", "status": STATUS_PASS, "policy_id": policy.policy_id}
        write_json(state_dir / "project.json", summary)
        _print_summary(summary)
        return 0

    if args.command == "inventory":
        policy = IntegrityPolicy.from_yaml(args.policy)
        rows = build_inventory(
            args.root,
            policy,
            omit_paths=_output_omit_paths(args.root, args.out),
        )
        write_inventory(rows, args.out)
        missing = sum(row["gate_status"] == "MISSING_REQUIRED" for row in rows)
        summary = {
            "command": "inventory",
            "status": STATUS_FAIL if missing else STATUS_PASS,
            "asset_count": len(rows),
            "missing_required": missing,
        }
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 2 if missing else 0

    if args.command == "freeze":
        policy = IntegrityPolicy.from_yaml(args.policy)
        summary = {"command": "freeze", **freeze_baseline(args.root, policy, args.baseline, force=args.force)}
        _print_summary(summary)
        return 0

    if args.command == "verify":
        result = verify_baseline(args.root, args.baseline)
        write_verification(result, args.out)
        summary = {key: value for key, value in result.items() if key != "results"}
        summary["command"] = "verify"
        _print_summary(summary)
        return 2 if result["gate_status"] == STATUS_FAIL else 0

    if args.command == "prediction-seal":
        seal = seal_prediction_declaration(
            read_json_strict(args.input, duplicate_key_code="PREDICTION_SEAL_INVALID_INPUT")
        )
        write_prediction_seal(seal, args.out, force=args.force)
        summary = {
            "command": "prediction-seal",
            "status": STATUS_PASS,
            "declaration_id": seal["declaration"]["declaration_id"],
            "declaration_sha256": seal["declaration_sha256"],
            "forced_overwrite": args.force,
        }
        _print_summary(summary)
        return 0

    if args.command == "prediction-verify":
        result = verify_prediction_seal(
            read_json_strict(args.input, duplicate_key_code="PREDICTION_SEAL_INVALID_INPUT"),
            read_json_strict(args.seal, duplicate_key_code="PREDICTION_VERIFY_MALFORMED_SEAL"),
        )
        summary = {"command": "prediction-verify", **result}
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 2 if result["status"] == STATUS_FAIL else 0

    if args.command == "isolation-audit":
        result = audit_isolation(
            args.root,
            read_json_strict(args.manifest, duplicate_key_code="ISOLATION_INVALID_MANIFEST"),
        )
        write_isolation_audit(result, args.out)
        summary = {"command": "isolation-audit", **result}
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 2 if result["status"] == STATUS_FAIL else 0

    if args.command == "evidence-index":
        result = build_evidence_index(
            read_json_strict(args.roles, duplicate_key_code="EVIDENCE_INDEX_INVALID_ROLES"),
            read_json_strict(args.records, duplicate_key_code="EVIDENCE_INDEX_INVALID_RECORDS"),
        )
        write_evidence_index(result, args.out)
        summary = {
            "command": "evidence-index",
            "status": result["status"],
            "counts": result["counts"],
            "limitation": result["limitation"],
        }
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 0

    if args.command == "support-audit":
        schema = read_yaml(args.schema) if args.schema else None
        summary = support_audit_report(
            args.data,
            _csv_list(args.features),
            discrete=_csv_list(args.discrete),
            schema=schema,
            out_dir=args.out,
        )
        summary["command"] = "support-audit"
        _print_summary(summary)
        return 0

    if args.command == "pareto-audit":
        rows = read_csv_rows(args.candidates)
        objectives = _objectives(args.objectives)
        pareto = validate_pareto_claims(rows, objectives, claimed_column=args.claimed_column)
        metrics = contamination_metrics(
            rows,
            support_column=args.support_column,
            selected_column=args.selected_column,
            pareto_column=args.claimed_column,
        )
        summary = {"command": "pareto-audit", "pareto": pareto, "contamination": metrics}
        Path(args.out).mkdir(parents=True, exist_ok=True)
        write_json(Path(args.out) / "pareto_audit.json", summary)
        _print_summary(summary)
        return 0

    if args.command == "split-audit":
        data = read_csv_rows(args.data)
        manifest = read_csv_rows(args.manifest)
        result = audit_split_leakage(
            data,
            manifest,
            id_column=args.id_column,
            coordinate_columns=_csv_list(args.coordinate_columns),
            group_column=args.group_column,
            time_column=args.time_column,
            branch_column=args.branch_column,
        )
        summary = {"command": "split-audit", **result}
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 2 if result["status"] == STATUS_FAIL else 0

    if args.command == "gate":
        result = evaluate_gate(read_json(args.metrics), read_yaml(args.policy))
        summary = {"command": "gate", **result}
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 2 if result["status"] in {STATUS_FAIL, STATUS_BLOCKED, STATUS_UNADJUDICATED} else 0

    if args.command == "deviation" and args.deviation_command == "record":
        row = record_deviation(args.out, read_yaml(args.config))
        summary = {
            "command": "deviation record",
            "status": STATUS_PASS,
            "deviation_id": row["deviation_id"],
        }
        _print_summary(summary)
        return 0

    if args.command == "claims" and args.claims_command == "evaluate":
        result = evaluate_claims(read_csv_rows(args.claims), read_csv_rows(args.evidence))
        Path(args.out).mkdir(parents=True, exist_ok=True)
        fields = [*CLAIM_FIELDS, "evidence_records_found", "evidence_records_requested"]
        write_csv_rows(Path(args.out) / "claim_evaluation.csv", result, fields)
        summary = {"command": "claims evaluate", "status": STATUS_PASS, "claim_count": len(result)}
        write_machine_summary(args.out, summary)
        _print_summary(summary)
        return 0
    raise InputValidationError("unknown command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rak", description="Audit scientific repository evidence-chain mechanics.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="initialize local audit metadata")
    init.add_argument("--root", required=True)
    init.add_argument("--policy", required=True)

    inventory = commands.add_parser("inventory", help="create repository inventory")
    inventory.add_argument("--root", required=True)
    inventory.add_argument("--policy", required=True)
    inventory.add_argument("--out", required=True)

    freeze = commands.add_parser("freeze", help="freeze a portable baseline")
    freeze.add_argument("--root", required=True)
    freeze.add_argument("--policy", required=True)
    freeze.add_argument("--baseline", required=True)
    freeze.add_argument("--force", action="store_true")

    verify = commands.add_parser("verify", help="verify a baseline")
    verify.add_argument("--root", required=True)
    verify.add_argument("--baseline", required=True)
    verify.add_argument("--out", required=True)

    prediction_seal = commands.add_parser("prediction-seal", help="seal an opaque prediction declaration")
    prediction_seal.add_argument("--input", required=True)
    prediction_seal.add_argument("--out", required=True)
    prediction_seal.add_argument("--force", action="store_true")

    prediction_verify = commands.add_parser("prediction-verify", help="verify a prediction declaration seal")
    prediction_verify.add_argument("--input", required=True)
    prediction_verify.add_argument("--seal", required=True)
    prediction_verify.add_argument("--out", required=True)

    isolation = commands.add_parser("isolation-audit", help="audit declared local workspace isolation")
    isolation.add_argument("--root", required=True)
    isolation.add_argument("--manifest", required=True)
    isolation.add_argument("--out", required=True)

    evidence_index = commands.add_parser("evidence-index", help="build a role-based evidence index")
    evidence_index.add_argument("--roles", required=True)
    evidence_index.add_argument("--records", required=True)
    evidence_index.add_argument("--out", required=True)

    support = commands.add_parser("support-audit", help="audit empirical feature support")
    support.add_argument("--data", required=True)
    support.add_argument("--features", required=True)
    support.add_argument("--discrete", default="")
    support.add_argument("--schema")
    support.add_argument("--out", required=True)

    pareto = commands.add_parser("pareto-audit", help="audit Pareto and support contamination")
    pareto.add_argument("--candidates", required=True)
    pareto.add_argument("--objectives", required=True)
    pareto.add_argument("--support-column", required=True)
    pareto.add_argument("--selected-column")
    pareto.add_argument("--claimed-column")
    pareto.add_argument("--out", required=True)

    split = commands.add_parser("split-audit", help="audit split metadata for leakage")
    split.add_argument("--data", required=True)
    split.add_argument("--manifest", required=True)
    split.add_argument("--id-column", required=True)
    split.add_argument("--coordinate-columns", default="")
    split.add_argument("--group-column")
    split.add_argument("--time-column")
    split.add_argument("--branch-column")
    split.add_argument("--out", required=True)

    gate = commands.add_parser("gate", help="evaluate a preregistered gate")
    gate.add_argument("--metrics", required=True)
    gate.add_argument("--policy", required=True)
    gate.add_argument("--out", required=True)

    deviation = commands.add_parser("deviation", help="manage protocol deviations")
    deviation_commands = deviation.add_subparsers(dest="deviation_command", required=True)
    deviation_record = deviation_commands.add_parser("record", help="append a deviation record")
    deviation_record.add_argument("--config", required=True)
    deviation_record.add_argument("--out", required=True)

    claims = commands.add_parser("claims", help="evaluate claim matrices")
    claim_commands = claims.add_subparsers(dest="claims_command", required=True)
    claim_evaluate = claim_commands.add_parser("evaluate", help="validate claims and evidence references")
    claim_evaluate.add_argument("--claims", required=True)
    claim_evaluate.add_argument("--evidence", required=True)
    claim_evaluate.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (
        AuditError,
        OSError,
        UnicodeError,
        ValueError,
        csv.Error,
        yaml.YAMLError,
    ) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
