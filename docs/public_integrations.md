# Public Integrations

This page records public, commit-bound evidence that a repository consumes a
released ResearchAuditKit artifact. It distinguishes a verified mechanical
integration from scientific-validity evidence or use by an unrelated organization.

```text
PUBLIC_CONSUMER_COUNT = 1
INDEPENDENT_EXTERNAL_CONSUMER_COUNT = 0
```

## CoordCap

| Field | Evidence |
| --- | --- |
| Consumer | CoordCap |
| Public URL | [ernestoleo777-dotcom/CoordCap](https://github.com/ernestoleo777-dotcom/CoordCap) |
| Owner relationship | `SELF_OWNED` |
| Consumer commit | [`719ee4e34aeb07357d097bb2bc0df1b80141e62a`](https://github.com/ernestoleo777-dotcom/CoordCap/commit/719ee4e34aeb07357d097bb2bc0df1b80141e62a) |
| ResearchAuditKit version | `v0.1.0-rc.2` |
| Installation authority | [GitHub RC2 wheel](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/tag/v0.1.0-rc.2) |
| Wheel SHA-256 | `71f905f3e39907c72c18e3d3207004f424c001238b103235a16484e1acace0fb` |
| Command | `rak inventory` |
| CI run | [`32759394362`](https://github.com/ernestoleo777-dotcom/CoordCap/actions/runs/32759394362) |
| CI conclusion | `success` |
| Integration scope | Mechanical repository-integrity preflight with a consumer-specific required-file policy |
| Non-implications | No scientific-validity judgment, claim verification, general reproducibility guarantee, or evidence of demand from an unrelated organization |

Classification:

```text
PUBLIC_INTEGRATION = VERIFIED
FIRST_VERIFIED_PUBLIC_CONSUMER = CoordCap
SELF_OWNED_PUBLIC_CONSUMER = TRUE
```

The cited workflow downloads the exact RC2 GitHub Release wheel, verifies its
SHA-256 before installation, checks `rak --version`, and executes `rak inventory`.
Its successful result establishes only that the declared mechanical preflight
passed at the cited consumer commit.
