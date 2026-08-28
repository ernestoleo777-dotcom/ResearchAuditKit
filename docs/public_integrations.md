# Public Integrations

This page records public, commit-bound evidence that a repository consumes a
released ResearchAuditKit artifact. It distinguishes a verified mechanical
integration from scientific-validity evidence or use by an unrelated organization.

```text
PUBLIC_CONSUMER_COUNT = 1
PUBLIC_RC3_ACTION_CONSUMER_COUNT = 1
SELF_OWNED_PUBLIC_CONSUMER_COUNT = 1
INDEPENDENT_EXTERNAL_CONSUMER_COUNT = 0
SCIENTIFIC_CERTIFICATION = FALSE
STABLE_RELEASE = NONE
```

## CoordCap

| Field | Evidence |
| --- | --- |
| Consumer | CoordCap |
| Public URL | [ernestoleo777-dotcom/CoordCap](https://github.com/ernestoleo777-dotcom/CoordCap) |
| Owner relationship | `SELF_OWNED` |
| Consumer commit | [`14cef46b3813e20ee26266faebb72a72aad7ac76`](https://github.com/ernestoleo777-dotcom/CoordCap/commit/14cef46b3813e20ee26266faebb72a72aad7ac76) |
| Consumer tree | `643f3e07de53c33ac522ab1885e7b705b75d7e06` |
| ResearchAuditKit version | [`v0.1.0-rc.3`](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/tag/v0.1.0-rc.3) |
| Immutable Action commit | [`72ee132038a36d8678da11e86d3b953726a5e9a7`](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/commit/72ee132038a36d8678da11e86d3b953726a5e9a7) |
| Interface | `rak audit` |
| Policy | `.rak/policy.yaml` |
| Action inputs | `path: .`; `policy: .rak/policy.yaml`; `fail-on: release-blocker`; `output-format: json` |
| CI run | [`33190211004`](https://github.com/ernestoleo777-dotcom/CoordCap/actions/runs/33190211004) |
| CI job | [`98913479499`](https://github.com/ernestoleo777-dotcom/CoordCap/actions/runs/33190211004/job/98913479499) |
| CI conclusion | `success` |
| Aggregate result | `PASS` |
| Findings | `PASS=8`; all other finding counts `0` |
| GitHub Job Summary | Rendered and verified |
| Integration scope | Mechanical repository-integrity preflight using the consumer's committed policy |
| Non-implications | No scientific-certification, scientific-correctness, claim-verification, general-reproducibility, or independent-adoption implication |

Classification:

```text
PUBLIC_INTEGRATION = VERIFIED
VERIFIED_PUBLIC_ACTION_CONSUMER = TRUE
FIRST_VERIFIED_PUBLIC_CONSUMER = CoordCap
SELF_OWNED_PUBLIC_CONSUMER = TRUE
INDEPENDENT_EXTERNAL_CONSUMER = FALSE
```

The cited current workflow invokes the released Action at the immutable RC3
commit and executes `rak audit`. Its successful result establishes only that the
declared mechanical preflight passed at the cited consumer commit.

## Historical integration lineage

The same consumer previously used the [RC2 GitHub Release
wheel](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/tag/v0.1.0-rc.2)
at commit
[`719ee4e34aeb07357d097bb2bc0df1b80141e62a`](https://github.com/ernestoleo777-dotcom/CoordCap/commit/719ee4e34aeb07357d097bb2bc0df1b80141e62a).
That workflow verified wheel SHA-256
`71f905f3e39907c72c18e3d3207004f424c001238b103235a16484e1acace0fb`
and ran `rak inventory`; its [historical successful
run](https://github.com/ernestoleo777-dotcom/CoordCap/actions/runs/32759394362)
remains valid evidence of the earlier integration stage. RC2 and RC3 are two
stages of one self-owned consumer integration, not two consumers.
