# RC2 Release Gates

```text
CURRENT_VERSION = 0.1.0rc2
CURRENT_RELEASE_CLASS = RELEASE_CANDIDATE
STABLE_RELEASE = NONE
DISTRIBUTION_AUTHORITY = GITHUB_RELEASES
PYPI_DISTRIBUTION = NONE
```

Release availability and downloadable artifacts are authoritative on the GitHub
Releases page. This document records the durable gates for an RC2 prerelease; it
does not declare the project stable or production-ready.

## Completed

- Public scope states mechanical verification and explicit scientific nonclaims.
- The source version is distinct from RC1 and identifies the RC2 candidate.
- A synthetic three-minute demo exercises a PASS and an intentional exit-2 finding.
- README, command, use-case, limitation, architecture, CI, release-delta, release-note,
  and distribution-audit documentation exists.
- The release process requires CI on Ubuntu with Python 3.10, 3.11, and 3.12.
- Python 3.12 build-test dependencies are explicit and the full matrix is green.
- Local candidate regression, build, distribution-content, and fresh-install checks
  are part of the release acceptance contract.

## Publication contract

- The exact tag target must pass remote CI on Python 3.10, 3.11, and 3.12.
- The tag must be annotated and peel to the exact CI-verified commit.
- Wheel and sdist assets must be rebuilt from that commit, fresh-installed, and
  bound to published checksums and a resolved release manifest.
- The GitHub release must be a prerelease, not a stable release.
- Package-index publication requires separate owner authorization.

## Unverified or not provided

- PyPI/TestPyPI distribution.
- Full Windows filesystem, shell, and installation acceptance.
- Performance or scale benchmarking.

## Release-critical

- Green remote CI for the exact tagged release commit on Python 3.10, 3.11, and
  3.12.
- Annotated-tag identity and GitHub prerelease metadata.
- Rebuild, checksum, install, CLI, and demo verification against the exact tag
  target and publicly downloaded assets.

## Noncritical

- Additional synthetic examples for every command.
- Richer terminal presentation or generated screenshots.
- Performance measurements without a current consumer requirement.

## Deferred

- Dashboard, hosted service, benchmark, and performance claims.
- New runtime/API behavior not required by the current release candidate.

## Consumer-dependent

- Any new command, output field, integration, or policy vocabulary must start from
  a concrete consumer workflow and compatibility requirement.
