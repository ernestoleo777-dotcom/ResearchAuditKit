# Use Cases

ResearchAuditKit is useful when a repository maintainer needs a local,
machine-readable preflight before sharing or evaluating an empirical project.

## Repository integrity preflight

Classify governed files, require named assets, store portable SHA-256 baselines,
and detect later mismatches, missing files, or unexpected scientific assets. This
can support a release checklist, but it does not show that file contents are
correct.

## Experiment-isolation checks

Check whether declared workspace directories exist, overlap, escape the declared
root, contain escaping symlinks, or disagree about shared paths. The audit is
structural; it does not prove user separation, permissions, or blinding.

## Portable-path validation

Use relative-path contracts in baselines, prediction declarations, and workspace
manifests to reject traversal and root escape. This is a file-layout control, not a
sandbox or operating-system access-control system.

## Evidence inventory

Build deterministic, role-labelled JSON/CSV indexes from supplied custody records.
The index makes asserted provenance easier to inspect without adjudicating the
evidence or its scientific meaning.

## Local seal and audit records

Seal an opaque declaration and later detect a byte-level declaration change.
Record protocol deviations, configured gate results, support summaries, Pareto
checks, and claim-to-evidence references as local auditable files.

## Deterministic CI checks

Run inventory, verification, isolation, prediction verification, split auditing,
or configured gates in CI and act on documented exit codes. Time, filesystem
metadata, and baseline identifiers can vary, so compare stable status/count fields
when byte identity is not part of the contract.

## Out of scope

Roadmap ideas are not current functionality. There is no all-in-one audit command,
experiment tracker, hosted service, dashboard, model evaluator, scientific reviewer,
or publication/acceptance predictor.
