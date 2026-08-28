# Project Status

```text
ENGINEERING_ASSET = MAINTAINED
OPERATING_MODE = CONSUMER_DRIVEN_MAINTENANCE
DISTRIBUTION_SOURCE_VERSION = 0.1.0rc3
PUBLIC_VERSION = 0.1.0rc3
RELEASE_TARGET = v0.1.0-rc.3
RELEASE_CLASS = GITHUB_PRERELEASE
PUBLIC_RELEASE_STATE = PRERELEASE
RELEASE_AVAILABILITY_AUTHORITY = GITHUB_RELEASES
RC3_RELEASED = VERIFY_GITHUB_RELEASES
STABLE_RELEASED = FALSE
STABLE_RELEASE = NONE
DISTRIBUTION_AUTHORITY = GITHUB_RELEASES
PYPI_DISTRIBUTION = NONE
PYPI_PUBLICATION = NONE
MARKETPLACE_PUBLICATION = NONE
SCIENTIFIC_METHOD_CLAIM = NONE
SCIENTIFIC_CERTIFICATION = FALSE
INDEPENDENT_PAPER_ROUTE = NONE
PUBLIC_INTEGRATION = VERIFIED
FIRST_VERIFIED_PUBLIC_CONSUMER = CoordCap
PUBLIC_CONSUMERS = 1
PUBLIC_RC3_ACTION_CONSUMERS = 1
SELF_OWNED_PUBLIC_CONSUMERS = 1
INDEPENDENT_EXTERNAL_CONSUMERS = 0
```

Release availability and downloadable artifacts are defined only by the
repository's GitHub Releases page. Version `0.1.0rc3` is published there as the
`v0.1.0-rc.3` prerelease; the annotated tag resolves to the public release
commit. The project has no stable release and is not distributed through PyPI,
TestPyPI, or GitHub Marketplace.

ResearchAuditKit supports mechanical, verifiable repository auditing, including:

- repository integrity;
- experiment isolation;
- custody and provenance records;
- evidence inventories;
- immutable-or-auditable record workflows under declared local contracts;
- deterministic validation.

ResearchAuditKit does not claim to determine:

- scientific truth;
- causal validity;
- novelty;
- project quality;
- acceptance probability;
- publication ceiling;
- whether a project should continue or stop.

Future functionality must be driven by a concrete consumer requirement. Maintenance does not imply an independent scientific-method claim or paper route.

The commit-bound [CoordCap public integration](docs/public_integrations.md) shows
the immutable RC3 Action running `rak audit` successfully in a real public
repository with its committed policy. CoordCap is the one self-owned public
consumer; the earlier RC2 workflow is historical lineage for that same
integration. This evidence does not establish scientific validity, general
reproducibility, independent demand, or use by an unrelated organization.
