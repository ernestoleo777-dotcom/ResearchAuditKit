# CLI Execution Report

## Result

`PASS`. Forty explicit command checks ran against the final wheel in an isolated environment.

- Top-level help and all 10 command help paths returned 0, including `deviation record` and `claims evaluate`.
- Each command family rejected missing required arguments with exit code 2.
- Invalid paths, malformed YAML, malformed JSON, duplicate-column CSV, and invalid objective syntax returned controlled errors without a Python traceback.
- Every successful functional command emitted a JSON machine summary and produced the documented files.
- A volatile metadata addition yielded `PASS_WITH_WARNINGS` and exit code 0.
- A governed scientific asset mismatch yielded `FAIL` and exit code 2.
- An existing baseline was refused without `--force`; forced replacement succeeded and every baseline row recorded `forced_overwrite=true`.
- Non-baseline report outputs are atomically replaced when explicitly rerun. Baselines have stricter overwrite protection.

The intentional leakage fixture returns 2 and is counted as a successful negative test. Full commands, expected/actual exit codes, summaries, and output paths are recorded in `COMMAND_EXECUTION_LOG.csv`.
