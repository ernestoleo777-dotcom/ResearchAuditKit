# Test Report

## Final result

`PASS — 90 passed, 0 failed, 0 skipped, 0 xfailed`

The complete pytest suite ran locally on CPU in 1.40 seconds with `PYTHONPATH=src`. It covers deterministic hashing, manifest self-exclusion, volatile warnings, scientific changes, missing files, overwrite safety, path portability, marginal/joint/conditional support, conservative missingness, candidate taxonomy, deterministic Pareto membership, contamination metrics, recommendation status, split leakage, calibration overlap, fold-local metadata, repeated-output determinism, every gate state, append-only deviations, claim status, CLI errors, and end-to-end source non-modification.

## Development disclosure

The first full run produced 89 passes and one failure. The privacy test searched the entire repository for a home-directory prefix while embedding that same prefix literally in its own source, creating a test self-reference. The test was corrected to construct the prefix from separate tokens. No production code or scientific threshold changed. The final complete run passed.

## Example execution

All five example directories were exercised through the CLI. Inventory/freeze/verify passed; conditional support and Pareto audits produced machine-readable output; the leakage example intentionally returned exit code 2; the gate example returned `INCONCLUSIVE` with exit code 0.

## Additional checks

Python bytecode compilation passed. Ruff was not installed in the local environment and was not downloaded; therefore no lint-pass claim is made.

