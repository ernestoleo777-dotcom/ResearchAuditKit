# RC1 to RC2 Delta

## Audit boundary

- RC1 tag: `v0.1.0-rc.1`
- RC1 annotated-tag object: `8aea415fe2908eb2466aa0cc9ca32a4e205b8d71`
- RC1 commit: `9ae2bfeead9cbf4c6779011b601666ffc0cff833`
- RC2 preparation parent: `7936913552a4ac0d53529d64793e45e8820f3609`
- Candidate version: `0.1.0rc2`

The audited parent contains eight commits after RC1: a versioned RC1 TestPyPI
workflow preparation, an extraction-plan record, custody/isolation runtime work,
prediction-seal guidance, acceptance evidence, public-scope alignment,
productization, and the Python 3.12 build-test dependency fix. The local release
preparation adds version, release documentation, status, packaging-list, manifest,
and test-authority changes only; it adds no runtime behavior.

## Implemented capabilities

### Runtime modules

- `integrity.prediction_seal` canonicalizes, hashes, writes, and verifies opaque
  declaration records. Matching establishes supplied-byte consistency only.
- `integrity.isolation` checks declared workspace structure, overlap, escaping
  symlinks, and reciprocal shared-path declarations.
- `integrity.portable` rejects absolute, escaping, and non-normalized portable
  references used by the new closed contracts.
- `governance.evidence_index` validates role-labelled records and emits deterministic
  JSON/CSV indexes and counts without adjudicating evidence quality.
- `io.json_io.read_json_strict` rejects duplicate object keys for the new closed
  JSON contracts.

### CLI commands

RC1 exposed ten top-level parsers. RC2 exposes those same ten plus:

- `rak prediction-seal`
- `rak prediction-verify`
- `rak isolation-audit`
- `rak evidence-index`

No RC1 command was removed or renamed. The argument definitions and handler code
for the ten shared commands are unchanged; the CLI diff adds imports, four command
branches, and four parser definitions. The package top-level export remains
`__version__` only. The new modules are importable implementation modules but no
new symbol was added to `research_audit_kit.__all__`.

### Validation and output behavior

- Prediction sealing writes a protected JSON seal and requires `--force` to replace
  it. Verification writes machine summaries and returns 2 on a digest mismatch.
- Isolation auditing writes `isolation_audit.json` plus summaries and returns 2 on
  structural findings.
- Evidence indexing writes JSON, CSV, and summaries; valid asserted records return
  0 because the command does not score evidence quality.
- Closed inputs for the four commands reject duplicate JSON keys, unsafe portable
  references, undeclared fields, duplicate identifiers, and invalid enumerations.
- Existing RC1 output schemas, overwrite rules, and exit-code branches were not
  changed by the post-RC1 CLI patch. The package/CLI version string changes from
  `0.1.0rc1` to `0.1.0rc2`.

## Packaging and CI

- Public package wording is narrowed to repository integrity, experiment isolation,
  evidence inventory, and auditable records.
- The sdist includes curated product documentation and the synthetic
  repository-integrity demo; the wheel remains runtime-focused.
- The existing `dev` extra now declares the PEP 517 frontend/backend tools used by
  distribution-content tests. They are not core runtime dependencies.
- Ordinary CI covers Python 3.10, 3.11, and 3.12 on Ubuntu. Preparation-parent run
  `32748703567` passed all matrix jobs, compile checks, and CLI smoke checks.
- The RC1 TestPyPI workflow remains deliberately hard-coded to RC1 artifacts and
  historical hashes. It is evidence and tooling for RC1, not an RC2 publisher.

## Tests

RC1 contains 116 collected tests. The green RC2 preparation parent contains 160
tests, adding synthetic coverage for the four commands, strict/path validation,
public documentation and demo replay, packaging content, version consistency,
collaboration templates, and the RC1-specific TestPyPI workflow. Release
preparation adds one manifest/status test without weakening or skipping an existing
test.

## Documentation and productization

RC2 adds a runnable three-minute synthetic demo, command reference, use cases,
limitations, architecture, CI integration, project/release status, collaboration
templates, and release documentation. The repository also contains engineering
plans and acceptance records; those records are not runtime features or evidence
of external effectiveness.

## Scope clarification

Public wording now describes deterministic mechanical checks. ResearchAuditKit
does not determine scientific validity, claim truth, causal validity, novelty,
project quality, publication merit, acceptance probability, or whether work should
continue. It provides no general reproducibility guarantee.

## Classification

| Change | Classification |
| --- | --- |
| Four new CLI commands and supporting modules | Implemented capability |
| Strict JSON and portable-reference checks used by those commands | Implemented capability |
| Green regression/build/demo/CI records | Accepted engineering evidence |
| README, references, examples, release notes, and collaboration templates | Documentation/productization change |
| Extraction plans, audit ledgers, and acceptance reports | Historical record, not user functionality |
| Windows validation, hosted services, dashboards, benchmarks, and new integrations | Future or deferred work |

## Known limitations

- Checks are limited to supplied files, metadata, and policies.
- Seals provide no trusted timestamp, authorship, or correctness proof.
- Isolation checks cannot establish human separation or access-control enforcement.
- Evidence indexes record assertions without adjudication.
- Windows remains unverified; the documented demo uses POSIX shell syntax.
- No external adoption, effectiveness, performance, or general reproducibility
  evidence is claimed.
