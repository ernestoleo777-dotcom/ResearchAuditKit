# ResearchAuditKit

An offline pre-release auditor for repository integrity, experiment isolation,
provenance records, and evidence inventories in empirical ML projects.

**Experimental — v0.1.0rc2.dev0 — no stable release**

[![CI](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml/badge.svg)](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Why ResearchAuditKit?

Research repositories often need a check that is narrower than scientific review
but stricter than a visual inspection. ResearchAuditKit records governed files,
detects missing or changed assets, checks declared isolation and provenance
contracts, and emits machine-readable findings suitable for local or CI preflight.
It runs locally and does not execute audited repository code.

## Three-minute Quick Start

Start from a source checkout with Python 3.10 or newer. PyYAML is the only runtime
dependency; installation may resolve it from your configured package source. The
audit commands themselves make no network calls.

<!-- quickstart-commands:start -->
```bash
python -m pip install -e .
rak --version
export RAK_DEMO_ROOT="$(mktemp -d)"
set -e
rak inventory --root examples/repository_integrity_demo/pass_repo --policy examples/repository_integrity_demo/policy.yaml --out "$RAK_DEMO_ROOT/pass"
set +e
rak inventory --root examples/repository_integrity_demo/issue_repo --policy examples/repository_integrity_demo/policy.yaml --out "$RAK_DEMO_ROOT/issue"
RAK_ISSUE_CODE=$?
set -e
test "$RAK_ISSUE_CODE" -eq 2
python -m json.tool "$RAK_DEMO_ROOT/pass/summary.json"
python -m json.tool "$RAK_DEMO_ROOT/issue/summary.json"
```
<!-- quickstart-commands:end -->

The second inventory intentionally returns exit code 2 because its synthetic
repository omits a policy-required `README.md`. Outputs remain under the temporary
directory named by `RAK_DEMO_ROOT`. See the
[step-by-step quickstart](docs/quickstart.md) and
[demo notes](examples/repository_integrity_demo/README.md).

## Example Output

These summaries are the real stable projections produced by the quickstart demo.
The PASS case contains all three governed files:

```json
{
  "asset_count": 3,
  "command": "inventory",
  "missing_required": 0,
  "status": "PASS"
}
```

The intentional issue is detected mechanically:

```json
{
  "asset_count": 3,
  "command": "inventory",
  "missing_required": 1,
  "status": "FAIL"
}
```

The complete inventory also records the missing path as `MISSING_REQUIRED`.
Checkout-dependent modification times and hashes are not presented as
byte-identical output.

## What It Checks

- repository inventories, required files, portable baselines, and byte changes;
- declared workspace isolation and relative-path safety;
- opaque declaration seals and supplied custody/provenance records;
- evidence inventories and claim-to-evidence references;
- empirical feature support and supplied Pareto/support labels;
- split metadata for declared leakage indicators;
- user-configured gates and protocol-deviation records.

Every result is local to the supplied files, metadata, and policy.

## What It Does Not Check

ResearchAuditKit does not determine scientific validity, claim truth, causal
validity, novelty, project quality, publication merit, acceptance probability, or
whether a research route should continue. It does not provide a general
reproducibility guarantee, execute models, inspect undocumented processing, or
establish an external timestamp or authority. A `PASS` means only that the
configured mechanical checks passed.

## Commands

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

All commands provide `--help` and a one-line JSON summary on stdout. Exit code 0
means the command completed without a failing mechanical gate; exit code 2 covers
detected failures, invalid inputs, and handled operational errors. Some report-only
commands describe findings without applying a failing gate. See the
[command reference](docs/command_reference.md) for exact arguments, outputs, exit
semantics, and overwrite behavior.

## CI Integration

The same synthetic demo can run in GitHub Actions without secrets, a GPU, or a
published package. Install from the checked-out source and assert both the PASS and
expected exit-2 case. A copy-paste workflow is available in
[CI integration](docs/ci_integration.md).

## Documentation

- [Quickstart](docs/quickstart.md)
- [Command reference](docs/command_reference.md)
- [Use cases](docs/use_cases.md)
- [Limitations](docs/limitations.md)
- [Architecture](docs/architecture.md)
- [CI integration](docs/ci_integration.md)
- [RC2 readiness register](docs/rc2_readiness.md)
- [Integrity model](docs/integrity_model.md)
- [Custody and isolation](docs/custody_isolation.md)
- [Empirical support audit](docs/support_audit.md)
- [Validation audit](docs/validation_audit.md)

## Development Status

ResearchAuditKit is an experimental, consumer-driven engineering asset.

Licensed under the Apache License, Version 2.0.

The current `0.1.0rc2.dev0` version is unreleased, a historical RC1 tag exists, and
the API is not committed to long-term stability.

Source-checkout installation is the supported evaluation path; no stable PyPI release is claimed.

Commands operate on local paths, but reports may reveal filenames and hashes.
Review generated artifacts before sharing them. See [Project Status](PROJECT_STATUS.md),
[Contributing](CONTRIBUTING.md), [Security](SECURITY.md), and the repository-root
[license](LICENSE).
