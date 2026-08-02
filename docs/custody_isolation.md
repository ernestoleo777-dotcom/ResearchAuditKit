# Custody and Isolation Commands

## Prediction declarations

Use `rak prediction-seal` to create a canonical seal from a JSON declaration with `declaration_id`, `declared_at`, and a non-empty `predictions` list. Each prediction has `prediction_id`, `subject_ref`, `prediction_value`, `producer_role`, and `method_version`. Fields are closed, prediction IDs are unique, opaque values must be JSON-compatible and finite, and path-like references must be normalized relative paths. The command refuses to replace an existing seal unless `--force` is explicit.

Use `rak prediction-verify` with the original declaration and seal. It writes a machine-readable summary and fails on declaration or sealing-metadata digest mismatch. A passing result means only that the supplied declaration matches the sealed content; it does not verify scientific correctness or independently trusted time ordering.

## Workspace isolation

Use `rak isolation-audit --root ROOT --manifest WORKSPACES.json --out DIR`. The manifest contains a positive integer `version` and non-empty `workspaces` list. Every workspace has `workspace_id`, `role`, and root-relative `path`; optional `allowed_inputs`, `allowed_outputs`, and `shared_with` declarations use normalized relative paths. `shared_with` is a mapping from another workspace ID to the same explicit shared-path list declared by that peer.

The audit reports missing directories, workspace overlap, root escape, escaping symlinks, and asymmetric shared declarations. It does not inspect user identity, permissions, process history, or scientific blinding.

## Role-based evidence index

Use `rak evidence-index --roles ROLES.json --records RECORDS.json --out DIR`. The roles document is `{ "roles": [...] }`; roles have `role_id` and `role_label`. The records document is `{ "records": [...] }`; records have `evidence_id`, `role_id`, `evidence_kind`, `subject_ref`, `recorded_at`, and `custody_status`.

Supported custody statuses are `DECLARED`, `SEALED`, `VERIFIED`, `UNVERIFIED`, and `RETIRED`. Output is sorted `evidence_index.json`, `evidence_index.csv`, and machine-readable summary files. The command records supplied metadata and does not judge evidence or claims.
