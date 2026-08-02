# Phase 1 Architecture

## Shared constraints

Phase 1 is a local-only, file-based extension. It adds no network call, GPU dependency, database, background worker, batch controller, migration action, or scientific evaluator. All records use UTF-8 JSON/CSV, deterministic ordering, opaque content fields, and relative paths where a path is needed. A custody `PASS` establishes only conformance to the declared contract; it never establishes scientific correctness, prediction quality, causal validity, or absence of undisclosed access.

Existing CLI contracts remain unchanged. Each new command writes the existing style of machine-readable summary and returns nonzero for contract failure; no current command gains new required flags or altered status semantics.

## Prediction seal

Use case: a project wants to declare a set of predictions before later review, comparison, or outcome availability and detect later edits to that declaration.

Proposed commands:

```text
rak prediction-seal --input DECLARATION.json --out SEAL.json
rak prediction-verify --input DECLARATION.json --seal SEAL.json --out DIR
```

Input contract:

- `declaration_id`, `declared_at`, and non-empty `predictions` are required.
- Each prediction requires a unique `prediction_id`, `subject_ref`, opaque `prediction_value`, `producer_role`, and `method_version`.
- `subject_ref` is an opaque identifier or portable relative path. Absolute paths, `..` escapes, duplicate identifiers, floating non-finite values, and undeclared fields are rejected.
- The command canonicalizes the approved schema with sorted keys and prediction identifiers. It records a SHA-256 digest, schema version, and locally observed sealing time.

Output contract: the sealed JSON stores the canonical declaration, digest, schema version, and sealing metadata. Verification writes `summary.json` with `PASS` or `FAIL`, observed digest, expected digest, and typed failures. It does not read outcomes, predictions from another project, or any scientific result.

Failure codes: `PREDICTION_SEAL_INVALID_INPUT`, `PREDICTION_SEAL_DUPLICATE_ID`, `PREDICTION_SEAL_UNSAFE_REFERENCE`, `PREDICTION_SEAL_UNSUPPORTED_VALUE`, `PREDICTION_VERIFY_MALFORMED_SEAL`, `PREDICTION_VERIFY_DIGEST_MISMATCH`, and `PREDICTION_VERIFY_SCHEMA_MISMATCH`.

Interaction: this complements `freeze`/`verify`. A user may inventory or freeze a resulting seal under their own integrity policy, but neither command is invoked implicitly. A valid seal proves byte-level declaration consistency, not that it predates an outcome in a trusted external clock, nor that its prediction is correct.

## Isolation audit

Use case: a project with multiple declared workspaces wants a structural check that role-labelled workspaces do not overlap, escape the supplied root, or use unsafe symlink routing.

Proposed command:

```text
rak isolation-audit --root ROOT --manifest WORKSPACES.json --out DIR
```

Input contract: the manifest contains a version, a list of unique `workspace_id` records, each with `role`, root-relative `path`, and optional root-relative `allowed_inputs`/`allowed_outputs`. Paths must be normalized relative paths. A workspace may declare `shared_with` identifiers only when both parties list the same explicit relative path. The audit root is supplied by the caller and is not serialized as a source-specific absolute path.

Output contract: `isolation_audit.json` contains sorted workspace findings, a summary by role, and status. The audit detects malformed declarations, missing workspace directories, duplicate or nested workspace paths, unsafe relative paths, symlinks resolving outside `--root`, and asymmetric shared-path declarations. It reports rather than changes files.

Failure codes: `ISOLATION_INVALID_MANIFEST`, `ISOLATION_DUPLICATE_WORKSPACE_ID`, `ISOLATION_UNSAFE_PATH`, `ISOLATION_WORKSPACE_MISSING`, `ISOLATION_WORKSPACE_OVERLAP`, `ISOLATION_SYMLINK_ESCAPE`, and `ISOLATION_SHARED_PATH_MISMATCH`.

Interaction: implement near current integrity path-safety utilities, sharing only clean-room helpers where their contracts already match. It does not replace `inventory`, `freeze`, `verify`, or `split-audit`. A structural pass cannot prove human-role separation, OS access-control enforcement, absence of copies, or scientific blinding.

## Evidence index

Use case: a project wants a deterministic, role-labelled catalogue of evidence records before claims evaluation, without adjudicating the evidence.

Proposed command:

```text
rak evidence-index --roles ROLES.json --records RECORDS.json --out DIR
```

Input contract: roles define unique `role_id` values and a human-readable `role_label`. Records define unique `evidence_id`, one declared `role_id`, an `evidence_kind`, an opaque `subject_ref`, a local `recorded_at` value, and a custody status from a small closed vocabulary. References are opaque identifiers or safe relative paths; record content and scientific conclusions are not required or parsed.

Output contract: `evidence_index.json`, `evidence_index.csv`, and `summary.json` contain sorted normalized records, role counts, evidence-kind counts, and validation status. It never promotes a record to a claim and never changes `claims evaluate` input requirements.

Failure codes: `EVIDENCE_INDEX_INVALID_ROLES`, `EVIDENCE_INDEX_INVALID_RECORDS`, `EVIDENCE_INDEX_DUPLICATE_ROLE_ID`, `EVIDENCE_INDEX_DUPLICATE_EVIDENCE_ID`, `EVIDENCE_INDEX_UNKNOWN_ROLE`, `EVIDENCE_INDEX_UNSAFE_REFERENCE`, and `EVIDENCE_INDEX_INVALID_CUSTODY_STATUS`.

Interaction: output can be manually transformed into existing claim-evaluation evidence input; no implicit pipeline or state transition is introduced. An indexed record is only an asserted custody record, not verified evidence and not a scientifically supported claim.

## Phase 2 boundary

The only documented later candidate is a read-only workspace census/archive controller. It must start from a fresh design review and cannot inherit movement, archival, rollback, platform-specific metadata, external pointer, Git, or absolute-path behavior from the source archive.
