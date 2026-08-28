# Research-release workflow

ResearchAuditKit organizes its primary product journey as `AUDIT → FREEZE → VERIFY → GATE`. Existing advanced commands remain available and unchanged.

| Stage | Command | When | Consumes | Emits | Cannot prove |
| --- | --- | --- | --- | --- | --- |
| Audit | `rak audit [PATH]` | Before preparing a public release | Local files; built-in or optional project policy | Human summary; optional `researchauditkit.audit/v1` JSON | Scientific correctness, reproducibility, completeness of undeclared intent |
| Freeze | `rak freeze` | After policy review and before release | Repository, explicit integrity policy | Portable baseline CSV and companion SHA-256 | Trusted time, authorship, semantic correctness |
| Verify | `rak verify` | Against a preserved baseline | Repository and baseline | Verification rows and summary | Why bytes changed or whether results remain scientifically valid |
| Gate | `rak gate` | Only when metrics and thresholds were separately declared | Metrics JSON and gate policy YAML | Gate summary | Whether thresholds are scientifically appropriate |

## Advanced/project-specific commands

`support-audit`, `pareto-audit`, `split-audit`, `prediction-seal`, `prediction-verify`, `isolation-audit`, `evidence-index`, `deviation record`, and `claims evaluate` require explicit domain/project inputs. `rak audit` does not invoke them automatically or infer those inputs.

## Preservation rule

An audit result is a preflight observation. A freeze is a content record. Verification compares against that record. A gate evaluates a declared policy. These records have different authority and must not be collapsed into a certification label.
