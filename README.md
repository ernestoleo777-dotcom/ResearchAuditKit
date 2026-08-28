# ResearchAuditKit

ResearchAuditKit is a local-first release-engineering and integrity toolkit for ML research repositories.

**Experimental — source version v0.1.0rc2 — release candidate — no stable release**

[![CI](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml/badge.svg)](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Audit and freeze an ML repository before public release

Install the current published RC2 authority by immutable asset URL and digest:

```bash
python -m pip install \
  "https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/download/v0.1.0-rc.2/research_audit_kit-0.1.0rc2-py3-none-any.whl#sha256=71f905f3e39907c72c18e3d3207004f424c001238b103235a16484e1acace0fb"
rak --version  # rak 0.1.0rc2
```

RC2 does not contain the hero command. From this unpublished owner-review source checkout:

```bash
python -m pip install -e .
rak audit .
```

`rak audit` inventories local files, applies universally observable checks, detects an optional `.rak/policy.yaml`, and reports mechanical warnings or release blockers. It does not execute repository code, upload source, call a network service, use a model, or require a GPU.

> **Publication status:** the current public distribution authority is the [GitHub Releases page](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases), specifically release [`v0.1.0-rc.2`](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/tag/v0.1.0-rc.2), whose wheel SHA-256 is `71f905f3e39907c72c18e3d3207004f424c001238b103235a16484e1acace0fb`. RC2 does **not** contain `rak audit`. This branch is an unpublished owner-review candidate; do not represent the hero command or Action as publicly released until a matching immutable artifact exists.

Real terminal output from the committed `pass_repo` fixture:

```text
ResearchAuditKit audit
Target: pass_repo
Policy: built-in (rak-generic-release-v1)
Result: PASS
Findings: PASS=6 WARNING=0 RELEASE_BLOCKER=0 NOT_APPLICABLE=2 UNRESOLVED=0
- No warnings, unresolved checks, or release blockers.
Boundary: PASS is mechanical only; it is not scientific correctness or certification.
```

`PASS` means only that the applicable local mechanical checks passed. It is not scientific correctness, reproducibility certification, paper validation, peer review, or an acceptance recommendation.

## Research-release lifecycle

```text
AUDIT → FREEZE → VERIFY → GATE
```

| Stage | Command | Purpose |
| --- | --- | --- |
| Audit | `rak audit .` | Find universally observable warnings/blockers and apply an optional project policy. |
| Freeze | `rak freeze ...` | Create a portable, policy-bound content baseline. |
| Verify | `rak verify ...` | Compare current governed bytes with the frozen baseline. |
| Gate | `rak gate ...` | Evaluate user-declared metrics against a user-declared gate policy. |

See the [workflow guide](docs/research_release_workflow.md) for consumed evidence, emitted records, and non-claims at each stage.

## Replay the hero workflow

The script below runs the current checkout, a clean fixture, a warning fixture, and an intentional configured blocker. It writes no audit output into the target repositories.

<!-- quickstart-commands:start -->
```bash
python -m pip install -e .
rak --version
rak audit .
rak audit examples/audit_demo/pass_repo
rak audit examples/audit_demo/warning_repo
set +e
rak audit examples/audit_demo/blocker_repo
RAK_BLOCKER_CODE=$?
set -e
test "$RAK_BLOCKER_CODE" -eq 2
```
<!-- quickstart-commands:end -->

The warning returns 0 under the default `--fail-on release-blocker`; use `--fail-on warning` to make warnings fail CI. `ABSTAIN`/`UNRESOLVED` and `RELEASE_BLOCKER` always return 2. See the [audit command contract](docs/audit_command.md) and [step-by-step quickstart](docs/quickstart.md).

## Project policy

With no configuration, `rak audit` applies the conservative built-in `rak-generic-release-v1` policy. A repository may provide `.rak/policy.yaml`, or pass `--policy PATH`, to replace inventory classification and declare required files. Universal path-safety, README/license presence, symlink reporting, and deterministic inventory checks still run.

Copy [the documented default policy](configs/audit_policy.default.yaml) to inspect the exact built-in contract. Policy files are data; the audit never runs target-project dependencies.

## Machine-readable output

```bash
rak audit . --format json --output audit-result.json
```

The canonical additive schema is [`researchauditkit.audit/v1`](schemas/audit-result-v1.schema.json). Findings use `PASS`, `WARNING`, `RELEASE_BLOCKER`, `NOT_APPLICABLE`, or `UNRESOLVED`; the aggregate result uses `PASS`, `WARNING`, `RELEASE_BLOCKER`, or `ABSTAIN`. Ordering and the content digest are deterministic for identical paths, bytes, and policy.

SARIF is deferred because its result/severity model cannot preserve `NOT_APPLICABLE`, `UNRESOLVED`, and the product's mechanical non-certification boundary without a documented mapping.

## GitHub Action

An unpublished composite Action source is included for owner review. It runs only `rak audit`, writes a GitHub Job Summary, preserves CLI exit status, requests no token, installs nothing, and does not execute target code. It must be pinned to an immutable commit/tag and requires Python 3.10+ plus PyYAML 6+ already available. See [GitHub Action integration](docs/github_action.md); do not advertise or publish it before a release artifact containing `rak audit` exists.

## Advanced commands

The front-door workflow does not remove or rename any existing command:

```text
rak init --root REPO --policy POLICY
rak inventory --root REPO --policy POLICY --out DIR
rak freeze --root REPO --policy POLICY --baseline FILE [--force]
rak verify --root REPO --baseline FILE --out DIR
rak prediction-seal --input DECLARATION.json --out SEAL.json [--force]
rak prediction-verify --input DECLARATION.json --seal SEAL.json --out DIR
rak isolation-audit --root ROOT --manifest WORKSPACES.json --out DIR
rak evidence-index --roles ROLES.json --records RECORDS.json --out DIR
rak support-audit --data CSV --features a,b --discrete a,b --out DIR
rak pareto-audit --candidates CSV --objectives loss:min,cost:min --support-column COLUMN --out DIR
rak split-audit --data CSV --manifest CSV --id-column ID --out DIR
rak gate --metrics JSON --policy YAML --out DIR
rak deviation record --config YAML --out LEDGER.csv
rak claims evaluate --claims CSV --evidence CSV --out DIR
```

These advanced commands require their documented inputs and are not guessed or automatically invoked by `rak audit`. Consult the [command reference](docs/command_reference.md).

## Public integration evidence

[CoordCap](https://github.com/ernestoleo777-dotcom/CoordCap) is the one verified public consumer. It is explicitly classified `SELF_OWNED_PUBLIC_CONSUMER`; its commit-bound RC2 integration runs `rak inventory`, not the unpublished hero command. This is not independent adoption. See [public integration evidence](docs/public_integrations.md).

## Documentation

- [Research-release workflow](docs/research_release_workflow.md)
- [Audit command](docs/audit_command.md)
- [Quickstart](docs/quickstart.md)
- [GitHub Action](docs/github_action.md)
- [Command reference](docs/command_reference.md)
- [CI integration](docs/ci_integration.md)
- [Extension boundaries](docs/extension_boundaries.md)
- [Limitations](docs/limitations.md)
- [Architecture](docs/architecture.md)
- [Public integrations](docs/public_integrations.md)
- [Project status](PROJECT_STATUS.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

ResearchAuditKit is an experimental, consumer-driven engineering asset. Licensed under the Apache License, Version 2.0. It has no stable release and is not distributed through PyPI or TestPyPI. Reports may reveal local filenames and hashes; review generated files before sharing them.
