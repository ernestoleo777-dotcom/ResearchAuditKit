# `rak audit` contract

## Invocation

```text
rak audit [PATH] [--policy POLICY] [--format human|json]
                 [--output RESULT.json] [--fail-on release-blocker|warning]
```

`PATH` defaults to `.`. The command writes nothing unless `--output` is supplied.

## Applied checks

The zero-configuration command reuses the existing inventory, policy, hashing, relative-path, and symlink-safety mechanisms. It performs only:

1. target directory readability;
2. deterministic path-ordered inventory and a timestamp-free content digest;
3. path confinement and escaping-symlink rejection;
4. repository-root README presence;
5. repository-root license-file presence;
6. in-root symlink reporting without following the target;
7. project-policy detection and declared required-file presence.

It deliberately does not inspect Git status, Git LFS payloads, large-file thresholds, absolute-path text, manifests, notebooks, environments, dependencies, models, data semantics, or scientific claims. Those checks were not part of the already-supported universal mechanism set and are not guessed in P1.

## Policy precedence

1. `--policy PATH`, resolved under normal CLI path rules, is authoritative when supplied.
2. Otherwise `PATH/.rak/policy.yaml` is auto-detected.
3. Otherwise the built-in `rak-generic-release-v1` policy is used.

A project policy replaces built-in inventory classification and required-file declarations. Universal checks listed above still apply. Missing/invalid explicit configuration produces `UNRESOLVED` and aggregate `ABSTAIN`; the command never silently falls back.

## Status and exit semantics

| Finding status | Meaning |
| --- | --- |
| `PASS` | Applicable mechanical check completed without a finding. |
| `WARNING` | Observable issue worth review but not a default blocker. |
| `RELEASE_BLOCKER` | Declared requirement or path-safety contract failed. |
| `NOT_APPLICABLE` | Optional mechanism/configuration did not apply. |
| `UNRESOLVED` | The command lacked enough safe local evidence to decide. |

Aggregate priority is `RELEASE_BLOCKER`, then `ABSTAIN` for unresolved checks, then `WARNING`, then `PASS`.

- default `--fail-on release-blocker`: exit 2 for `RELEASE_BLOCKER` or `ABSTAIN`; warnings return 0;
- `--fail-on warning`: warnings also return 2;
- handled input/operational errors retain the existing exit-2 contract.

## Result schema

[`schemas/audit-result-v1.schema.json`](../schemas/audit-result-v1.schema.json) is additive and versioned. It records target identifier, policy source, aggregate status, complete counts, ordered findings, inventory count/digest, and fixed limitations. It intentionally omits timestamps, absolute target paths, and a numeric score.

## Non-claims

`PASS` is not proof of scientific correctness, reproducibility, replicability, paper validity, peer-review acceptance, complete operating-system isolation, trusted timing, or claim truth.
