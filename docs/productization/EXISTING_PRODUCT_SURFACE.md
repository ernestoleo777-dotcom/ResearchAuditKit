# Existing Product Surface

This record describes ResearchAuditKit at `0.1.0rc2.dev0` before the portfolio
productization work. It is based on the installed `rak` parser, command handlers,
tests, examples, packaging configuration, and GitHub workflows.

## Working user operations

- Install the package from a source checkout on Python 3.10 or newer when PyYAML is
  available.
- Run all commands locally without a runtime network call.
- Inventory repository files under a declared integrity policy.
- Freeze and verify portable, relative-path baselines.
- Seal and verify opaque prediction declarations without interpreting outcomes.
- Check declared workspace isolation and create role-labelled evidence indexes.
- Audit supplied support tables, Pareto claims, split metadata, configured gates,
  protocol deviations, and claim-to-evidence references.
- Consume JSON, YAML, and CSV output, plus one-line JSON summaries on stdout.

`rak init` is optional. It creates `.rak/project.json`; the remaining commands do
not require initialization.

## CLI command inventory

| Command | Required arguments | Optional arguments | Primary files | Exit behavior |
| --- | --- | --- | --- | --- |
| `init` | `--root`, `--policy` | none | `ROOT/.rak/project.json` | 0 on creation; 2 on handled error or existing state |
| `inventory` | `--root`, `--policy`, `--out` | none | `inventory.csv`, `inventory.json`, `summary.json`, `summary.yaml` | 0 on PASS; 2 when required files are missing or input fails |
| `freeze` | `--root`, `--policy`, `--baseline` | `--force` | baseline CSV and `.sha256` companion | 0 on success; 2 on handled error or refused overwrite |
| `verify` | `--root`, `--baseline`, `--out` | none | `verification.csv`, `summary.json` | 0 on PASS/warnings; 2 on FAIL or input error |
| `prediction-seal` | `--input`, `--out` | `--force` | seal JSON | 0 on success; 2 on invalid input or refused overwrite |
| `prediction-verify` | `--input`, `--seal`, `--out` | none | `summary.json`, `summary.yaml` | 0 on PASS; 2 on mismatch or invalid input |
| `isolation-audit` | `--root`, `--manifest`, `--out` | none | `isolation_audit.json`, `summary.json`, `summary.yaml` | 0 on PASS; 2 on structural failure or invalid input |
| `evidence-index` | `--roles`, `--records`, `--out` | none | `evidence_index.json`, `evidence_index.csv`, summary JSON/YAML | 0 on valid index; 2 on invalid input |
| `support-audit` | `--data`, `--features`, `--out` | `--discrete`, `--schema` | `observed_combinations.csv`, `support_summary.json` | 0 on valid report; 2 on invalid input |
| `pareto-audit` | `--candidates`, `--objectives`, `--support-column`, `--out` | `--selected-column`, `--claimed-column` | `pareto_audit.json` | 0 on valid report; 2 on invalid input |
| `split-audit` | `--data`, `--manifest`, `--id-column`, `--out` | coordinate, group, time, and branch columns | `summary.json`, `summary.yaml` | 0 on PASS; 2 on detected leakage or invalid input |
| `gate` | `--metrics`, `--policy`, `--out` | none | `summary.json`, `summary.yaml` | 0 on PASS/INCONCLUSIVE/SKIPPED; 2 on FAIL/BLOCKED/UNADJUDICATED or input error |
| `deviation record` | `--config`, `--out` | none | deviation ledger CSV | 0 on append; 2 on invalid input |
| `claims evaluate` | `--claims`, `--evidence`, `--out` | none | `claim_evaluation.csv`, `summary.json`, `summary.yaml` | 0 on valid evaluation; 2 on invalid input |

Argparse help and version exits use their standard 0/2 behavior. All handled
runtime errors are emitted as JSON on stderr with exit code 2.

## Output and overwrite boundaries

- Summary JSON is key-sorted and human-readable files are UTF-8.
- CSV output neutralizes spreadsheet formula prefixes.
- Ordinary report files are atomically replaced on rerun.
- Baselines and prediction seals refuse replacement unless `--force` is explicit.
- Forced baseline/seal replacement is reported; `init` refuses an existing state.
- Baseline identifiers, creation times, file modification times, and hashes are
  intentionally variable. Status/count projections can still be deterministic for
  fixed synthetic inputs.

## Installation and packaging boundary

- Canonical entry point: `rak = research_audit_kit.cli:main`.
- Supported metadata: Python `>=3.10`; CI currently exercises 3.10, 3.11, and 3.12.
- Runtime dependency: PyYAML 6 or newer.
- No stable release or supported PyPI install is claimed. The working public path
  is a source checkout with an editable install.
- Wheel and sdist builds succeed locally. Before productization, the sdist prunes
  public docs and examples, while the wheel contains package code and license
  material but not repository-level examples.

## Existing documentation and examples

Focused documents already cover integrity, empirical support, optimization,
validation, gate semantics, protocol deviations, custody, and isolation. Existing
synthetic examples exercise integrity, support, leakage, configured gates, Pareto
audits, and custody commands. They do not yet provide one tested, front-door flow
with both a PASS and an intentionally detected mechanical problem.

## Operations that do not exist

- There is no `rak audit`, `rak scan`, or all-in-one project command.
- There is no dashboard, hosted service, background process, model execution, or
  repository code execution.
- There is no remote timestamp authority, identity verification, access-control
  enforcement, or continuous experiment tracker.
- There is no scientific-validity, causal-validity, novelty, publication,
  acceptance, project-quality, or continue/stop evaluator.
- There is no general reproducibility guarantee.

## Productization gaps

1. README navigation starts with boundaries rather than a runnable user outcome.
2. No single three-minute demo proves both success and finding behavior.
3. Command arguments, output files, and exit semantics are not consolidated.
4. CI integration is not documented as a copy-paste consumer workflow.
5. Curated public docs/examples are not included in the sdist.
6. Repository issue and pull-request templates are absent.
7. Link, demo, public-document, and distribution-content acceptance checks are not
   consolidated in one productization test module.

The gaps can be addressed with documentation, synthetic fixtures, packaging
selection, and tests. No new runtime/API behavior is required.
