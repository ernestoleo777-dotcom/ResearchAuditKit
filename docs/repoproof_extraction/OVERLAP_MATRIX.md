# Overlap Matrix

The JSON file is authoritative for the structured matrix. Percentages are behavior-level estimates rather than copied-code or line-count comparisons.

| Candidate | Existing RAK equivalent | Overlap | Unique value | Decision |
|---|---|---:|---|---|
| Content baseline verification | inventory / freeze / verify | 100% | none | `ALREADY_COVERED_DO_NOT_IMPORT` |
| Prediction-first seal | freeze | 55% | sealed prediction declaration | `NEW_GENERAL_MODULE` |
| Workspace isolation audit | inventory containment; split-audit metadata checks | 45% | multi-workspace boundary audit | `EXTEND_EXISTING_MODULE` |
| Role-based evidence index | claims evaluate; deviation ledger | 40% | role registry and deterministic index | `NEW_GENERAL_MODULE` |
| Deterministic serialization | stable hashing and JSON output | 100% | none | `ALREADY_COVERED_DO_NOT_IMPORT` |
| Authority failure taxonomy | gates, claims, limitations | 25% | not safely separable | `REJECT_PROJECT_SPECIFIC` |
| Git custody snapshot | content inventory only | 15% | later provenance option | `DOCUMENTATION_ONLY` |
| Workspace census/archive controller | single-root inventory/verify | 30% | Phase 2 read-only census option | `DOCUMENTATION_ONLY` |

Only the three Phase 1 rows satisfy the gate after their stated clean-room rewrites. The controller remains a documented Phase 2 candidate and is not an approved migration workflow.
