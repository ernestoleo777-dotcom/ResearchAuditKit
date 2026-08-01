# Changelog

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
