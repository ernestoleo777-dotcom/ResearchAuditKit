# TestPyPI Trusted Publishing Setup

This procedure prepares a manual TestPyPI upload of the exact audited GitHub RC1 assets. It does not publish from the workflow commit and it does not rebuild the package.

## Pending Trusted Publisher

Create a TestPyPI Pending Trusted Publisher with these exact values:

| Setting | Value |
| --- | --- |
| Project name | `research-audit-kit` |
| GitHub owner | `ernestoleo777-dotcom` |
| Repository | `ResearchAuditKit` |
| Workflow filename | `publish-testpypi.yml` |
| Environment | `testpypi` |

All values must match exactly. In the TestPyPI UI, use only the workflow filename unless the UI explicitly requests a different form. A pending publisher does not reserve the package name before a first upload. No API token is needed, and no token should be placed in GitHub secrets.

## GitHub environment

Create the `testpypi` environment in the repository Settings. Restrict deployment branches to `main`, or to selected branches/tags that include only `main`. If the repository plan and collaborator arrangement support a trusted reviewer, consider an approval rule. A solo maintainer should not add a reviewer rule that cannot be satisfied. Do not create a PyPI or TestPyPI token secret.

## Supply-chain boundary

The workflow is manually dispatched from `main`, but it publishes only the pre-existing `v0.1.0-rc.1` GitHub Pre-release assets after verifying the release type, annotated-tag peeled commit, asset names, `SHA256SUMS`, fixed hashes, and package metadata. Its `dist/` directory contains exactly the verified wheel and sdist. It never builds a package.

## Authorized execution order

1. Merge this workflow preparation commit and confirm ordinary `main` CI is green.
2. Create the GitHub `testpypi` environment.
3. Create the TestPyPI Pending Trusted Publisher using the five values above.
4. Return and explicitly state: `已完成 TestPyPI Trusted Publisher 配置，授权运行一次 TestPyPI 发布 workflow`.
5. Only after that explicit authorization may the workflow be manually dispatched once.
6. Verify TestPyPI installation, metadata, README rendering, license, wheel/sdist behavior, and Python 3.10/3.11/3.12 smoke checks.

This workflow is not for production PyPI and does not configure any PyPI account or repository setting.
