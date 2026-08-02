# Source Asset Index

## Audit boundary

This is a clean-room planning audit. It records behavior-level observations only; no source code, fixtures, expected output, prediction, oracle, evaluator, protocol, schema, scientific result, metric, real data, or absolute path was copied into this repository.

The source archive is closed and states that its scientific accuracy is not determinable. Its custody methods are therefore treated only as engineering inspiration, never as scientific evidence.

## Read assets

All paths below are relative to the read-only archive root.

| Asset | Permitted purpose | Planning observation | Used for |
|---|---|---|---|
| `README.md` | archive status and permitted use | permits general audit-tool extraction; forbids continuing the research mainline | boundary |
| `ARCHIVE_STATUS.md` | closure state | reports closed/recommended-for-archive status and no source deletion | boundary |
| `WORKSPACE_INDEX.md` | role index | records custody categories and workspace roles without establishing scientific validity | isolation/index concepts |
| `CATEGORY_GUIDE.md` | category meaning | labels infrastructure as reusable custody, validator, freeze, and determinism tooling | candidate discovery |
| `00_FINAL_DECISIONS/.../REPOPROOF_V21_FINAL_CLOSEOUT_REPORT.md` | closeout | historical values cannot support accuracy evidence | claim boundary |
| `00_FINAL_DECISIONS/.../SALVAGEABLE_ASSET_REGISTRY.md` | salvage registry | identifies prediction-first workflow, reviewer isolation, deterministic serialization, and custody methods as non-scientific salvage candidates | Phase 1 discovery |
| `00_FINAL_DECISIONS/.../SALVAGEABLE_ASSETS.md` | salvage registry | identifies custody, access logging, taxonomy, and authority-only tooling as engineering artifacts | exclusions and boundary |
| `00_FINAL_DECISIONS/.../V22_MVP_STOP_DECISION.md` | stop decision | prohibits a new protocol/schema/evaluator patch loop | exclusion |
| `MANIFESTS/README.md` | controller index | distinguishes controller utilities from experimental tools | controller classification |
| `MANIFESTS/MANIFEST_REORGANIZATION_MAP.md` | migration description | describes byte-preserving controller-file moves | Phase 2 only |
| `MANIFESTS/tools/consolidate.py` | generic controller script | behavior includes read-only census, relative custody facts, symlink/worktree checks, collision blocking, and post-move comparison; it is path- and platform-coupled | Phase 2 candidate only |
| `MANIFESTS/tools/tidy_controller.py` | role/index controller script | behavior includes category/role indexing and non-destructive controller reports; it contains archive-specific labels and paths | evidence-index concept only |

The required general failure taxonomy was not present as a standalone, safely identifiable asset under `20_REQUIRED_FAILURE_EVIDENCE` during this audit. It was not inferred from failure fixtures or other prohibited material and contributes no implementation requirement.

## Explicitly not read

- Fixture inputs, expected outputs, oracles, predictions, reviewer/adjudication material, agreement results, and all `F01`–`F36` content.
- Engine, protocol, schema, evaluator, scientific implementation, metrics, and real data.
- Any asset outside the permitted archive paths.

## Current RAK evidence

The following was verified from this repository, not assumed from this request:

- `rak inventory`, `freeze`, and `verify` are implemented in `src/research_audit_kit/cli.py` and integrity modules, use relative paths and SHA-256, reject escaping symlinks, and emit CSV/JSON summaries.
- `support-audit`, `pareto-audit`, `split-audit`, `gate`, `deviation record`, and `claims evaluate` are registered CLI commands.
- The claims evaluator validates evidence identifiers, while the deviation ledger is append-only.
- Machine-readable outputs are written by current command paths; runtime dependencies are local Python and PyYAML only.
- The release record reports 109 passing tests, Apache-2.0 licensing, and CI configuration that is present but not remotely executed. The repository currently contains 25 top-level test modules and GitHub Actions workflows for CI and TestPyPI.
