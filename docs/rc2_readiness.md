# RC2 Readiness Register

```text
RC2_READINESS = NOT_DETERMINED
RELEASE_AUTHORIZATION = NONE
CURRENT_VERSION = 0.1.0rc2.dev0
```

This register separates local productization evidence from release authorization.
It does not declare RC2 ready.

## Completed

- Public scope states mechanical verification and explicit scientific nonclaims.
- Canonical development version no longer reuses RC1 for different code.
- A synthetic three-minute demo exercises a PASS and an intentional exit-2 finding.
- README, command, use-case, limitation, architecture, and CI documentation exist.
- Issue and pull-request templates request reproducible consumer context.
- Local regression, build, distribution-content, and fresh-install checks are part
  of the productization acceptance plan.

## Blocked

- Remote CI evidence for the local productization commit cannot exist until that
  commit is reviewed and separately authorized for push.
- RC2 tag, GitHub release, and package publication are blocked on explicit owner
  authorization and a separate release-preparation review.

## Not attempted

- Creating `v0.1.0-rc.2` or changing the development version to `0.1.0rc2`.
- GitHub Release, PyPI, TestPyPI, Pages, or another hosted deployment.
- Full Windows filesystem/PowerShell acceptance.
- Performance or scale benchmarking.

## Release-critical

- Owner review of the local portfolio-productization commit.
- Green CI on the reviewed commit for Python 3.10, 3.11, and 3.12.
- A fresh artifact build, installation, CLI/demo smoke, metadata inspection, and
  recorded artifact digests from the exact proposed release commit.
- Final confirmation that version, changelog, citation, tag target, release notes,
  and publication workflow describe the same immutable code.
- Explicit authorization for RC2 release preparation; this document is not that
  authorization.

## Noncritical

- Additional synthetic examples for every command.
- Richer terminal presentation or generated screenshots.
- More output-schema narrative beyond the current command reference.

## Desirable

- Test the public quickstart on an additional POSIX platform and a clean Windows
  environment.
- Collect consumer feedback on which mechanical checks are most useful in CI.

## Deferred

- Dashboard, hosted service, benchmark, and performance claims.
- New runtime/API behavior not required by the current executable demo.

## Consumer-dependent

- Any new command, output field, integration, or policy vocabulary must start from
  a concrete consumer workflow and compatibility requirement.
