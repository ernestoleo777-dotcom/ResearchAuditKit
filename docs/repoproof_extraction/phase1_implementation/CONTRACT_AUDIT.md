# Contract Audit

## Prediction seal and verify

The declaration schema is closed and requires `declaration_id`, `declared_at`, and a non-empty prediction list. Each prediction is closed, has the five specified fields, rejects duplicate IDs, accepts opaque JSON-compatible values only, rejects non-finite floats and unsupported objects, and never interprets a value or reads an outcome.

Path-like references reject absolute paths, traversal, and non-normalized components; opaque identifiers remain unopened strings. Canonical declarations sort prediction IDs and use stable object hashing. Locally observed `sealed_at` is excluded from the declaration digest. A separate seal digest covers sealing metadata so metadata mutation is detected. Existing seal files refuse replacement unless `--force` is explicit.

All required failure codes are implemented: `PREDICTION_SEAL_INVALID_INPUT`, `PREDICTION_SEAL_DUPLICATE_ID`, `PREDICTION_SEAL_UNSAFE_REFERENCE`, `PREDICTION_SEAL_UNSUPPORTED_VALUE`, `PREDICTION_VERIFY_MALFORMED_SEAL`, `PREDICTION_VERIFY_DIGEST_MISMATCH`, and `PREDICTION_VERIFY_SCHEMA_MISMATCH`.

## Workspace isolation audit

The manifest is closed, has a positive version and non-empty workspace list, and validates unique workspace IDs, safe relative workspace/allowed/shared paths, missing directories, lexical and resolved-path overlap, escaping symlinks, containment, and reciprocal shared declarations. The audit only reads local structure and emits a report; it creates, moves, copies, deletes, or changes no workspace file.

All required failure codes are implemented: `ISOLATION_INVALID_MANIFEST`, `ISOLATION_DUPLICATE_WORKSPACE_ID`, `ISOLATION_UNSAFE_PATH`, `ISOLATION_WORKSPACE_MISSING`, `ISOLATION_WORKSPACE_OVERLAP`, `ISOLATION_SYMLINK_ESCAPE`, and `ISOLATION_SHARED_PATH_MISMATCH`.

## Role-based evidence index

Roles and records use separate closed documents. The index checks unique IDs, declared roles, safe references, and the closed custody vocabulary: `DECLARED`, `SEALED`, `VERIFIED`, `UNVERIFIED`, and `RETIRED`. It outputs sorted JSON and CSV plus a summary with role, kind, and custody-status counts. It does not read evidence content, invoke claim evaluation, infer permission, or adjudicate a record.

All required failure codes are implemented: `EVIDENCE_INDEX_INVALID_ROLES`, `EVIDENCE_INDEX_INVALID_RECORDS`, `EVIDENCE_INDEX_DUPLICATE_ROLE_ID`, `EVIDENCE_INDEX_DUPLICATE_EVIDENCE_ID`, `EVIDENCE_INDEX_UNKNOWN_ROLE`, `EVIDENCE_INDEX_UNSAFE_REFERENCE`, and `EVIDENCE_INDEX_INVALID_CUSTODY_STATUS`.

## Claim boundary

All public documentation and result limitations state that a pass is only local contract conformance. It does not establish prediction correctness, trusted timing, independent authorship, human separation, access control, absence of copies, evidence validity, claim support, provenance verification, or scientific truth.

Result: `CONTRACT_PASS`.
