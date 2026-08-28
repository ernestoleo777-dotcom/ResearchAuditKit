# Changelog

## Unreleased

- Add the zero-configuration `rak audit [PATH]` front door with conservative
  built-in policy, optional `.rak/policy.yaml`, human output, and versioned
  `researchauditkit.audit/v1` JSON.
- Organize the primary product journey as `AUDIT → FREEZE → VERIFY → GATE` while
  preserving every existing command and schema.
- Prepare an unpublished composite GitHub Action that performs no install/upload,
  does not execute target code, preserves CLI exit status, and writes a safe Job
  Summary.
- Add deterministic PASS, WARNING, and RELEASE_BLOCKER fixtures and replays.
- Reject non-portable or symlink-escaping `policy.required_files` entries before
  inventory, hashing, serialization, or baseline creation; diagnostics retain the
  list index and stable reason code without echoing the rejected value.
- Document CoordCap as the first verified, self-owned public consumer of the RC2
  GitHub Release wheel and bind the record to its exact commit and successful
  `rak inventory` workflow run.
- Clarify that this public integration is mechanical evidence only and does not
  establish scientific validity, general reproducibility, independent demand, or
  use by an unrelated organization.
- No version, tag, release, push, Marketplace, or package publication change.

## 0.1.0rc2 — 2026-08-25

- Finalize version and publication metadata for the `v0.1.0-rc.2` GitHub
  prerelease.
- Add local-only prediction sealing and verification for opaque declarations.
- Add structural workspace isolation auditing and role-based evidence indexing.
- Reject duplicate keys in the closed JSON contracts used by the new commands and
  validate portable relative references.
- Rework the public entry point around a tested three-minute source-checkout demo.
- Add consolidated command, use-case, limitation, architecture, CI, release-delta,
  and distribution documentation.
- Add consumer-focused issue/PR templates and package curated public docs plus the
  synthetic integrity demo in the sdist.
- Declare the build frontend and backend tools used by package-content tests so the
  Python 3.10-3.12 CI matrix does not depend on runner-preinstalled packaging tools.
- Clarify the public scope as mechanical repository auditing rather than scientific
  or research-decision evaluation.
- Mark the project as experimental and maintained in response to concrete consumer
  requirements.
- Add clean-room synthetic tests and custody/isolation documentation with explicit non-scientific claim boundaries.
- Add no scientific interpretation, predictive scoring, recommendation, or
  decision-making capability.

## 0.1.0rc1 — Release Candidate 1

- Select Apache-2.0 and add the verified standard `LICENSE` text.
- Add Apache-2.0 packaging metadata and document the current NOTICE decision.
- Integrate SPDX license identifiers into maintained package source files.
- Revalidate distribution license inclusion and prepare local GitHub handoff material.

- Add Python 3.10-compatible TOML parsing for release-metadata tests.
- Declare the conditional test dependency on `tomli` for Python versions below 3.11.
- Update CI to install the declared development extra.
- Initialize independent package architecture.
- Add integrity, support, optimization-result, validation, governance, reporting, and CLI utilities.
- Add synthetic fixtures, examples, tests, and clean-room audit records.
- Use the package constant as the single version source for build metadata and CLI output.
- Harden CSV validation, atomic writes, baseline self-exclusion, symlink handling, and CLI errors.
- Add release-risk tests, minimal CI configuration, and publication-readiness audit records.
