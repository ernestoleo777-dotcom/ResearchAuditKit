# Clean-Room Plan

## Boundary decision

Status: `PASS`

The target repository was absent at the start. The protected source scientific baseline was independently rechecked: all 33 governed scientific assets matched. Only high-level governance and transfer-boundary documents were consulted.

## Permitted conceptual inputs

- Versioned scientific-asset policies and warning/failure separation.
- Relative-path inventories, immutable baselines, and pre/post verification.
- Marginal, joint, conditional, and structural-missingness audits.
- Pareto-support contamination and recommendation-support audits.
- Split, leakage, fold-local metadata, and determinism checks.
- Preregistered gates, claim matrices, deviation ledgers, and negative-result preservation.

## Prohibited inputs

No original datasets, problem attachments, papers, model files, numeric results, recommendation coordinates, domain-specific terminology, unadjudicated outputs, old source implementations, old comments, or old fixtures may enter this repository.

## Implementation method

1. Design task-independent dataclasses and file formats.
2. Implement every module from its public behavioral contract using Python standard-library facilities plus PyYAML.
3. Test only with newly authored repository, optimizer-configuration, Pareto, leakage, and protocol-deviation fixtures.
4. Scan the completed tree for forbidden names, paths, hashes, serialized models, and inherited claims.
5. Recheck the protected source baseline after all work.
6. Initialize an independent Git repository without any inherited history or remote.

## Claim boundary

The package audits evidence-chain mechanics. It cannot establish scientific truth, physical feasibility, true performance, absence of misconduct, or publication readiness. A gate PASS means only that declared criteria passed.

## Publication boundary

The code may reach `GITHUB_READY_ENGINEERING_TOOL` only if independence, correctness, claim safety, reusability, and publication safety all pass; tests and the forbidden-asset scan must also pass. License selection remains a user decision.

