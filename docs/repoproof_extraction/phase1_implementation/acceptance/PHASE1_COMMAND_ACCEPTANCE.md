# Phase 1 command acceptance

## Authority and basis

This is the post-fix authoritative acceptance review for Phase 1. It evaluates
implementation commit `bced122b8ad8506cd9f35a72e217d1fa9ace45ea` plus P1 fix
commit `346c0425ecae161dc57e9d7d057b2cdf18f52986`. The P1 commit received a
green CI matrix for Python 3.10, 3.11, and 3.12 before this rerun.

All demonstrations used newly created synthetic temporary material. No source
archive content was read or executed for this review.

## User-facing command review

All four help pages returned zero. The documented synthetic command sequence
completed successfully for `prediction-seal`, `prediction-verify`,
`isolation-audit`, and `evidence-index`, with their expected machine-readable
summaries and documented output files.

The acceptance rerun covered:

- prediction sealing, verification, reordered declarations, nested opaque
  values, duplicate IDs, unsafe references, non-finite values, malformed and
  changed seals, and repeated digest generation;
- existing-output refusal, explicit replacement, preservation of the rejected
  target bytes, preservation of an unrelated file, and verification after an
  explicit replacement;
- disjoint and shared workspaces; asymmetric sharing, missing directories,
  overlaps, traversal, and symlink escape;
- sorted evidence indexes; duplicate roles and records, unknown roles, invalid
  custody status, unsafe references, and malformed documents;
- 1, 100, and 1000-item synthetic smoke cases for each capability; and
- repeated deterministic command and library checks.

The overwrite refusal exits nonzero and reports both that the seal already
exists and that `--force` is required to replace it. It does not overwrite,
delete, or create a backup by default. With an explicit `--force`, only the
named output is replaced and the resulting seal verifies successfully.

## Claim boundaries

Acceptance does not treat a passing command as a scientific conclusion.
Prediction sealing establishes supplied declaration consistency only; it is not
a correctness finding, an authorship finding, or trusted time ordering.
Isolation auditing checks declared local path structure only; it is not human
separation, access-control enforcement, absence of copies, or blinding.
Evidence indexing records supplied metadata only; it is not evidence
adjudication, externally verified provenance, claim support, or scientific
truth.

## Gates

| Gate | Result | Basis |
|---|---|---|
| A1 Functional | PASS | Positive and negative synthetic command paths passed. |
| A2 Usability | PASS | All core scores are at least 3/5; overwrite guidance is 5/5. |
| A3 Safety | PASS | Relative-reference checks, symlink escape checks, refusal-by-default, and side-effect checks passed. |
| A4 Claim boundary | PASS | Help, documentation, outputs, and module limitations remain bounded. |
| A5 Documentation | PASS | The custody demo commands match the installed CLI. |
| A6 Determinism | PASS | Reordered declaration, index ordering, and findings ordering checks passed repeatedly. |
| A7 Regression | PASS | 149 local tests and the P1 Python 3.10/3.11/3.12 CI matrix passed. |
| A8 Release integrity | PASS | RC1 remains unchanged; same-version republication is disallowed; no publishing workflow was run. |

Decision: `PHASE1_ACCEPTED_READY_FOR_RC2_PLANNING`.
