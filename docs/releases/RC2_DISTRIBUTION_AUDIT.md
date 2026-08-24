# RC2 Distribution Audit

Audit date: 2026-08-25

Authority scope: prepublication distribution audit. This is a historical snapshot
of preparation-time state, not the current release-status authority. Current tags,
release metadata, and downloadable assets are authoritative on GitHub Releases.

## Package identity

| Surface | Value |
| --- | --- |
| Distribution metadata name | `research-audit-kit` |
| Import package | `research_audit_kit` |
| Console script | `rak` |
| Candidate version | `0.1.0rc2` |
| Candidate tag | `v0.1.0-rc.2` |
| Build backend | `setuptools.build_meta` with `setuptools>=68` |
| Core runtime dependency | `PyYAML>=6.0` |

## GitHub workflows

The ordinary `CI` workflow runs on push and pull requests with `contents: read`.
It installs `.[dev]`, runs the full suite, compiles `src`, and smokes `rak --help`
on Ubuntu with Python 3.10, 3.11, and 3.12. It does not build a release artifact,
create a tag/release, request OIDC, or publish a package.

`publish-testpypi.yml` is manual-only and grants `contents: read` plus
`id-token: write` to its single `testpypi` environment job. Every provenance,
filename, version, commit, and digest guard is hard-coded to RC1. It downloads the
existing RC1 GitHub prerelease assets and can publish only those assets to
TestPyPI. It must remain RC1-specific historical tooling and is not an RC2 path.

No workflow creates GitHub releases or RC2 artifacts. No RC2 workflow is added by
this preparation because the current safe path is explicit local build, exact
commit CI, owner-reviewed tag, and owner-authorized GitHub prerelease. Creating a
new publication workflow without configured environments and a publication
decision would be speculative.

## Existing release and environment state at audit time

- GitHub prerelease `v0.1.0-rc.1` exists with its historical wheel, sdist, and
  `SHA256SUMS` assets.
- The public repository reports no configured GitHub Actions environments through
  the repository API. The documented `testpypi` environment is therefore not
  currently ready.
- The RC2 tag and GitHub release do not exist.

## PyPI and TestPyPI

The public JSON endpoints for `research-audit-kit` returned HTTP 404 on both PyPI
and TestPyPI. This finds no public distribution conflict, but a 404 does not prove
that the normalized name can be claimed, that an owner account controls it, or
that a pending trusted publisher is configured.

```text
PYPI_STATUS = PYPI_OWNER_ACTION_REQUIRED
PYPI_PUBLICATION = NOT_AUTHORIZED
TESTPYPI_PUBLICATION = NOT_AUTHORIZED
```

Owner action is required to decide whether either package index is in scope, verify
account/name availability in the service UI, create the relevant GitHub environment,
and configure a trusted publisher. No token, account, project, publisher, or
environment was created or modified during this audit.

## Future authorized GitHub prerelease sequence

The following is a plan, not authorization. Substitute the reviewed local release
commit reported by the preparation task for `RELEASE_COMMIT`.

```bash
RELEASE_COMMIT=<reviewed-release-commit>
test "$(git rev-parse HEAD)" = "$RELEASE_COMMIT"
git push origin main
# Wait for the exact commit's Python 3.10/3.11/3.12 CI to pass.
git tag -a v0.1.0-rc.2 "$RELEASE_COMMIT" -m "ResearchAuditKit v0.1.0-rc.2"
git push origin v0.1.0-rc.2
gh release create v0.1.0-rc.2 \
  --repo ernestoleo777-dotcom/ResearchAuditKit \
  --verify-tag \
  --prerelease \
  --title "ResearchAuditKit v0.1.0-rc.2" \
  --notes-file docs/releases/v0.1.0-rc.2.md \
  research_audit_kit-0.1.0rc2-py3-none-any.whl \
  research_audit_kit-0.1.0rc2.tar.gz \
  SHA256SUMS
```

Before those commands, rebuild the two distributions from the exact reviewed
commit in a clean source tree, regenerate `SHA256SUMS`, fresh-install the wheel,
and compare package metadata, CLI version, demo behavior, filenames, sizes, and
hashes with the approved evidence. Package-index publication, if later chosen,
requires a separate authorization after the GitHub prerelease is verified.
