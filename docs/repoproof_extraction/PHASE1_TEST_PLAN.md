# Phase 1 Test Plan

All fixtures will be newly authored, synthetic, small, and local to this repository. No source-archive asset, identifier, metric, data value, prediction, expected result, or scientific content may appear in tests.

| Capability | Positive synthetic tests | Negative synthetic tests | Compatibility checks |
|---|---|---|---|
| Prediction seal | identical logical declarations produce stable canonical seals; a newly written seal verifies; arbitrary opaque values are preserved | duplicate ID, missing required field, absolute/escaping reference, non-finite number, malformed seal, changed value, changed metadata, digest mismatch | existing freeze/verify still pass; seal can be independently inventoried without self-reference |
| Isolation audit | two disjoint role-labelled synthetic folders pass; symmetric explicit shared path passes; stable sorted findings | duplicate ID, missing folder, absolute path, `..` escape, nested overlap, escaping symlink, asymmetric shared declaration | existing inventory symlink and safe-relative tests remain unchanged; no source tree mutation |
| Evidence index | two roles and sorted records produce stable JSON/CSV and accurate counts; opaque identifier references pass | duplicate role/evidence ID, unknown role, invalid custody status, malformed record, unsafe path | existing claims evaluate accepts its current files unchanged; no automatic claims integration |

## Required assertions

- CLI help exposes only the planned command names and required arguments.
- Each failure code is emitted in both machine-readable output and a nonzero exit path.
- Repeated runs over equivalent logical input have deterministic output apart from explicitly documented local timestamps; timestamp fields are excluded from content digest input.
- All new tests run offline with the existing Python/PyYAML dependency set.
- A regression run covers the current suite, CLI synopsis test, SPDX/header policy, and no-network scan.
- Test comments and fixture names state that custody outcomes are not scientific validity outcomes.

## Acceptance rule

Implementation is eligible only after all three command families have complete synthetic positive, negative, determinism, CLI, and backward-compatibility coverage. The plan itself authorizes none of this implementation.
