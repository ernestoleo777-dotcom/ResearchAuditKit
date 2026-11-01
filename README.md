# ResearchAuditKit

English | [简体中文](README.zh-CN.md)

**Know which research claims need review when your artifacts change.**

Track explicitly listed result files, connect them to your own claims, and see
review paths when files change or disappear. Runs locally without executing your
project, uploading files, calling a model or requiring a GPU.

**Experimental — release candidate v0.1.0rc4 — GitHub prerelease — no stable release**

[![CI](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml/badge.svg)](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Install

The [GitHub Releases page](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases)
is the distribution authority. Verify the RC4 release assets against its SHA256SUMS,
then install in your Python environment:

```bash
python -m pip install "https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/download/v0.1.0-rc.4/research_audit_kit-0.1.0rc4-py3-none-any.whl"
rak --version  # rak 0.1.0rc4
```

ResearchAuditKit is not distributed through PyPI or TestPyPI. Install may fetch
PyYAML; evidence checks themselves are local. For a reviewed source checkout:

```bash
python -m pip install -e .
```

## First project: list → capture → check

From your project directory, start the guide:

```bash
rak evidence wizard
```

Name a result file and enter its relative path. Optionally write a claim and
explicitly name the assets supporting or contradicting it. Preview and confirm.
The guide writes a new `assets.json`; it never scans your project or reads assets.

```bash
rak evidence init --manifest assets.json --out graph.json --format json
```

Save the receipt's `graph_content_sha256` separately as your reviewed baseline
anchor. Replace `SAVED_DIGEST` and the optional claim ID below with your values:

```bash
rak evidence check graph.json --graph-sha256 SAVED_DIGEST --allow-unresolved-claim urn:rak:project:claim:main@1 --format markdown --out check.json
```

Omit the allowance if you declared no claim. It accepts only that exact Claim's
unresolved declaration; other missing or unresolved evidence still blocks.
Outputs are exclusive new files; use a new report name for each local rerun.

A changed result file produces this kind of report (synthetic example):

| Problem file | Observation | Claim to review |
| --- | --- | --- |
| results.csv | IDENTITY_MISMATCH | main@1 |

Declared path: results.csv → listed evidence → main@1.
Review the file change and declaration before deliberately updating the baseline.
Matching bytes do not establish claim truth. Relationships are supplied by you.

[Actual synthetic demo report](examples/evidence_graph_demo/expected_guided_report.md) ·
[Five-minute guide and GitHub Job Summary](docs/evidence_onboarding.md) ·
[Anchored CI checks](docs/evidence_check.md) ·
[Replayable synthetic demo](examples/evidence_graph_demo/README.md)

## Audit and freeze an ML repository before public release

The existing repository audit remains available with no required configuration:

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

`rak audit` inventories local files and applies mechanical checks and an optional
`.rak/policy.yaml`. PASS is not scientific correctness or reproducibility certification.
See the [audit quickstart](docs/quickstart.md).

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

Every `policy.required_files` value must be a canonical, POSIX-style relative
file path confined to the repository. Absolute, traversal, backslash, control-
character, non-canonical, and symlink-escaping values are rejected as policy
errors without reproducing the unsafe value.

Copy [the documented default policy](configs/audit_policy.default.yaml) to inspect the exact built-in contract. Policy files are data; the audit never runs target-project dependencies.

## Machine-readable output

```bash
rak audit . --format json --output audit-result.json
```

The canonical additive schema is [`researchauditkit.audit/v1`](schemas/audit-result-v1.schema.json). Findings use `PASS`, `WARNING`, `RELEASE_BLOCKER`, `NOT_APPLICABLE`, or `UNRESOLVED`; the aggregate result uses `PASS`, `WARNING`, `RELEASE_BLOCKER`, or `ABSTAIN`. Ordering and the content digest are deterministic for identical paths, bytes, and policy.

SARIF is deferred because its result/severity model cannot preserve `NOT_APPLICABLE`, `UNRESOLVED`, and the product's mechanical non-certification boundary without a documented mapping.

## GitHub Action

The composite Action self-provisions a fixed Python runtime and hash-locked
PyYAML dependency, runs only `rak audit`, writes a GitHub Job Summary, preserves
CLI exit status, requests no token, and does not install or execute target code.
Bootstrap requires official Action and package infrastructure; the audit itself
remains local and uploads no repository content. After confirming the RC4
prerelease exists, use the exact versioned ref:

```yaml
- uses: ernestoleo777-dotcom/ResearchAuditKit@v0.1.0-rc.4
  with:
    path: .
    fail-on: release-blocker
```

No mutable `v0`, `v0.1`, `main`, or `latest` Action alias is published. Users
seeking maximum immutability may replace the tag with its resolved commit SHA.
See [GitHub Action integration](docs/github_action.md).

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

[CoordCap](https://github.com/ernestoleo777-dotcom/CoordCap) is the first and
currently only verified public consumer. At its [consumer merge
commit](https://github.com/ernestoleo777-dotcom/CoordCap/commit/14cef46b3813e20ee26266faebb72a72aad7ac76),
this self-owned integration—not independent external adoption—pins the
[v0.1.0-rc.3](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/tag/v0.1.0-rc.3)
Action to its [immutable release
commit](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/commit/72ee132038a36d8678da11e86d3b953726a5e9a7),
runs `rak audit` with the committed
`.rak/policy.yaml`, and uses ResearchAuditKit only as a mechanical
repository-integrity preflight. The [successful public-main
run](https://github.com/ernestoleo777-dotcom/CoordCap/actions/runs/33190211004)
reported aggregate `PASS` and rendered a GitHub Job Summary. See [public
integration evidence](docs/public_integrations.md).

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
- [First-party candidate release preflight](docs/release_evidence_preflight.md)
- [Project status](PROJECT_STATUS.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

ResearchAuditKit is an experimental, consumer-driven engineering asset. Licensed under the Apache License, Version 2.0. It has no stable release and is not distributed through PyPI or TestPyPI. Reports may reveal local filenames and hashes; review generated files before sharing them.

## Evidence graph

`rak evidence` adds an explicit, versioned evidence graph alongside the existing audit commands.
Use `rak evidence validate graph.json`, `rak evidence trace CLAIM_ID --graph graph.json`,
`rak evidence doctor graph.json`, or `rak evidence impact graph.json`. The additive schema is `researchauditkit.evidence/v1`.
Relationships and verification labels in input are user declarations. A matching file hash is
mechanical evidence of current bytes; it is not scientific adjudication or historical identity.
Start with [asset-list initialization and readable reports](docs/evidence_onboarding.md),
or replay the [synthetic CLI demo](examples/evidence_graph_demo/README.md).
Use [anchored project checks](docs/evidence_check.md) to gate listed file identities in CI while retaining unresolved claim declarations.
See [Evidence Graph B1](docs/evidence_graph.md) for paths, limits, exits and uncertainty.
The evidence commands are included in RC4.
