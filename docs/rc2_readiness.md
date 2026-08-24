# RC2 Readiness Register

```text
RC2_READINESS = LOCAL_CANDIDATE_PREPARED
RELEASE_AUTHORIZATION = NONE
CURRENT_VERSION = 0.1.0rc2
CURRENT_RELEASE_CLASS = RELEASE_CANDIDATE
REMOTE_RELEASE = NOT_YET_PUBLISHED
EXACT_RELEASE_COMMIT_CI = PENDING
```

This register separates local release-candidate preparation from public release
authorization. It does not declare RC2 published, stable, or production-ready.

## Completed

- Public scope states mechanical verification and explicit scientific nonclaims.
- The source version is distinct from RC1 and identifies the RC2 candidate.
- A synthetic three-minute demo exercises a PASS and an intentional exit-2 finding.
- README, command, use-case, limitation, architecture, CI, release-delta, release-note,
  and distribution-audit documentation exists.
- The preparation parent passed CI on Ubuntu with Python 3.10, 3.11, and 3.12.
- Python 3.12 build-test dependencies are explicit and the full matrix is green.
- Local candidate regression, build, distribution-content, and fresh-install checks
  are required before the preparation commit is created.

## Blocked

- Exact release-commit CI cannot exist until the local preparation commit is
  reviewed and separately authorized for push.
- The RC2 tag, GitHub prerelease, and any package-index publication require separate
  owner authorization.
- PyPI/TestPyPI ownership and trusted-publisher configuration require owner action.

## Not attempted

- Creating or pushing `v0.1.0-rc.2`.
- Creating an RC2 GitHub Release or publishing to PyPI/TestPyPI.
- Full Windows filesystem, shell, and installation acceptance.
- Performance or scale benchmarking.

## Release-critical

- Owner review of the local release-preparation commit.
- Green remote CI for the exact reviewed release commit on Python 3.10, 3.11, and
  3.12.
- Explicit authorization for the annotated tag and GitHub prerelease.
- Rebuild and checksum verification against the exact authorized tag target.

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
