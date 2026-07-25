# Dependency Audit

## Result

`PASS_WITH_ENVIRONMENT_NOTES`.

| Class | Declaration | Local evidence | Assessment |
| --- | --- | --- | --- |
| Build | setuptools >=68 | 82.0.1 | Used by local backend builds |
| Runtime | PyYAML >=6.0 | 6.0.3 | Imported for `safe_load`; minimal and not narrowly pinned |
| Development | pytest >=8 | 9.1.1 | Test-only extra |
| Development | pre-commit >=3 | not checked | Optional tooling only |
| Development | ruff >=0.6 | not installed | Correctly optional; marked not run |

No GPU, cloud, database, web, telemetry, or deep-learning dependency is declared. Static import review found no unused runtime dependency and no vendored third-party implementation. pip and Python were 26.0.1 and 3.13.13 for the final local installs.

Python 3.10 compatibility was checked by parsing all package modules with the Python 3.10 grammar. Runtime tests were executed locally on Python 3.13.13. Python 3.10–3.12 execution is configured in CI but was not remotely run, so this report does not falsely claim those interpreters were tested locally.

`ruff` and `mypy` were `NOT_AVAILABLE_IN_CURRENT_ENVIRONMENT`; they were not installed. `compileall`, pytest, import, package install, and CLI checks passed.

No online vulnerability database was queried.
