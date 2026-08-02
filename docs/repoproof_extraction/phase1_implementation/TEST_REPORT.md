# Test Report

## Targeted verification

- `tests/test_prediction_seal.py`, `tests/test_isolation.py`, and `tests/test_evidence_index.py`: 26 passed.
- Those three modules plus `tests/test_cli.py`: 42 passed.
- The targeted suites were repeated three times: 26 passed on each run.

Coverage includes closed schemas, duplicate keys/IDs, unsafe paths, non-finite values, malformed and modified seals, workspace overlap, symlink escape, reciprocal sharing, role validation, custody vocabulary, deterministic ordering, output collision behavior, machine-readable CLI errors, and the synthetic command demo.

## Full regression

- `python -m pytest -q`: 149 passed, 0 failed, 0 skipped, 0 xfailed.
- `python -m compileall -q src tests`: passed.
- `python -m pip check`: passed.
- Package import and top-level CLI help: passed.

The only correction cycle addressed three in-scope audit findings: seal-output overwrite protection and metadata integrity, custody-status counts, and prohibited test terminology. No assertion was removed or weakened.

Result: `TEST_PASS`.
