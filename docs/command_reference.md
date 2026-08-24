# Command Reference

The canonical executable is `rak`, provided by
`research_audit_kit.cli:main`. Use `rak --version`, `rak --help`, and
`rak COMMAND --help` to inspect the installed parser.

All successful command handlers emit one compact JSON object on stdout. Handled
errors emit JSON on stderr and return 2. Output paths are created as needed.

| Command | Required arguments | Optional arguments | Written output | Exit and overwrite behavior |
| --- | --- | --- | --- | --- |
| `rak init` | `--root ROOT --policy POLICY` | none | `ROOT/.rak/project.json` | 0 on creation; 2 if `.rak` exists or input fails. Never replaces existing state. |
| `rak inventory` | `--root ROOT --policy POLICY --out DIR` | none | `inventory.csv`, `inventory.json`, `summary.json`, `summary.yaml` | 0 when required files are present; 2 when any are missing or input fails. Reports are atomically replaced. |
| `rak freeze` | `--root ROOT --policy POLICY --baseline FILE` | `--force` | baseline CSV and `FILE.sha256` | 0 on success; 2 on error. Existing baseline/companion is refused unless `--force`; forced replacement is recorded. |
| `rak verify` | `--root ROOT --baseline FILE --out DIR` | none | `verification.csv`, `summary.json` | 0 on PASS or warnings; 2 on FAIL/error. Reports are replaced. |
| `rak prediction-seal` | `--input JSON --out JSON` | `--force` | canonical seal JSON | 0 on success; 2 on invalid input/refused overwrite. Existing seal requires `--force`. |
| `rak prediction-verify` | `--input JSON --seal JSON --out DIR` | none | `summary.json`, `summary.yaml` | 0 on supplied-byte match; 2 on mismatch/error. Reports are replaced. |
| `rak isolation-audit` | `--root ROOT --manifest JSON --out DIR` | none | `isolation_audit.json`, `summary.json`, `summary.yaml` | 0 on declared structural PASS; 2 on structural failure/error. |
| `rak evidence-index` | `--roles JSON --records JSON --out DIR` | none | `evidence_index.json`, `evidence_index.csv`, summary JSON/YAML | 0 for a valid index; 2 on invalid input. It does not gate evidence quality. |
| `rak support-audit` | `--data CSV --features CSV_LIST --out DIR` | `--discrete CSV_LIST`, `--schema YAML` | `observed_combinations.csv`, `support_summary.json` | 0 for a valid report; 2 on invalid input. Descriptive support findings are not a failing gate. |
| `rak pareto-audit` | `--candidates CSV --objectives NAME:min,... --support-column COLUMN --out DIR` | `--selected-column`, `--claimed-column` | `pareto_audit.json` | 0 for a valid report; 2 on invalid input. Supplied objectives/labels are not validated as truth. |
| `rak split-audit` | `--data CSV --manifest CSV --id-column COLUMN --out DIR` | `--coordinate-columns`, `--group-column`, `--time-column`, `--branch-column` | `summary.json`, `summary.yaml` | 0 on PASS; 2 on detected declared leakage/error. |
| `rak gate` | `--metrics JSON --policy YAML --out DIR` | none | `summary.json`, `summary.yaml` | 0 for PASS, INCONCLUSIVE, or SKIPPED; 2 for FAIL, BLOCKED, UNADJUDICATED, or error. |
| `rak deviation record` | `--config YAML --out CSV` | none | deviation ledger CSV | 0 on append; 2 on invalid input. Existing rows are read and rewritten with the appended record. |
| `rak claims evaluate` | `--claims CSV --evidence CSV --out DIR` | none | `claim_evaluation.csv`, `summary.json`, `summary.yaml` | 0 for a valid evaluation; 2 on invalid input. It checks references/status rules, not claim truth. |

## Machine-readable status boundary

Statuses include `PASS`, `PASS_WITH_WARNINGS`, `INCONCLUSIVE`, `FAIL`, `BLOCKED`,
`SKIPPED_BY_GATE`, and `UNADJUDICATED`, plus command-specific finding codes. Their
meaning is defined by the local command and policy. A status is not a scientific,
publication, or project-quality judgment.

## Filesystem and safety behavior

- Paths stored in baselines are relative and SHA-256 digests cover bytes.
- Inventory does not execute repository code.
- Escaping symlinks and unsafe normalized paths are rejected where applicable.
- JSON/YAML/CSV inputs are parsed as data; model serialization formats are not
  loaded.
- Report output generally replaces files atomically. The explicit baseline/seal
  exceptions protect existing records by default.
