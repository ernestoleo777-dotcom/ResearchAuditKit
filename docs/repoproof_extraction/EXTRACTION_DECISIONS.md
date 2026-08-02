# Extraction Decisions

Status: `FROZEN` — implementation is not authorized by this plan.

| Capability | Decision | Rationale |
|---|---|---|
| Prediction-first sealing | `NEW_GENERAL_MODULE` | Extends file baselines with a compact canonical declaration and verifier, without interpreting outcomes. |
| Workspace isolation audit | `EXTEND_EXISTING_MODULE` | Reuses containment and safe-relative-path conventions while adding declared workspace boundaries. |
| Role-based evidence index | `NEW_GENERAL_MODULE` | Builds a role registry and index; current claim evaluation only checks supplied evidence references. |
| Workspace census/archive controller | `DOCUMENTATION_ONLY` | Deferred to Phase 2; only a future read-only census may be reconsidered. |
| Content baselines and deterministic serialization | `ALREADY_COVERED_DO_NOT_IMPORT` | Current inventory, freeze, verify, hashing, and sorted JSON cover the general behavior. |
| Historical authority failure taxonomy | `REJECT_PROJECT_SPECIFIC` | It remains coupled to the closed project's authority/evaluator context. |
| Git custody snapshot | `DOCUMENTATION_ONLY` | Useful only as a future, separately designed provenance option. |

Every Phase 1 capability passed the decision gate: it has a cross-project use case, no imported source state, fully synthetic tests, a local lightweight API, and no implication of scientific correctness.
