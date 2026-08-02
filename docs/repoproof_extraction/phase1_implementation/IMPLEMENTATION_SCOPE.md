# Implementation Scope

Implemented commands:

- `rak prediction-seal`
- `rak prediction-verify`
- `rak isolation-audit`
- `rak evidence-index`

The implementation consists of local JSON/CSV contracts, deterministic normalization, SHA-256 sealing, structural path checks, and synthetic examples/tests. Existing commands are not changed in meaning and none invokes a new command implicitly.

Excluded Phase 2 and prohibited work remains unimplemented: workspace census/archive control, file movement/copy/deletion, rollback, provenance snapshots, authority taxonomies, review workflows, scientific evaluators, benchmarks, remote services, databases, and batch orchestration.
