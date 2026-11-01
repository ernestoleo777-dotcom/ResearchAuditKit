# First-party candidate release evidence preflight

The `Release evidence preflight` workflow applies AuditKit's evidence graph to
AuditKit's own newly built wheel and source distribution. It is a first-party
engineering integration using real candidate build files. It does not validate
an already published release, add an independent consumer, or publish a package.
The candidate retains the checkout's source version. Review that version and
its release contract before tagging; a successful candidate check is not publication.

## Separate capture and check stages

1. Build the candidate wheel and source distribution in a new runner directory.
2. Capture their explicit filenames with the asset-list initializer, generating
   a graph and an initialization receipt. Retain the receipt SHA-256 separately
   in the CI step output.
3. Install that wheel into a fresh environment with offline/no-dependency
   installation. System packages supply existing dependencies; the job explicitly
   verifies that AuditKit itself imports from the new environment's package path.
4. Run doctor and impact from that wheel-installed library. Compare the captured
   receipt to the separately supplied digest, and compare the graph and asset
   manifest to their captured identities.
5. Fail closed on missing, changed, unidentifiable or empty candidate files,
   changed baselines, additional findings, incomplete impact analysis or unsafe
   paths. Write portable JSON receipts and a GitHub Job Summary.

The gate accepts only the explicitly generated two-asset contract. Its one Claim
remains DECLARED/UNRESOLVED. The policy allows that exact unresolved declaration
while requiring all file identity checks and the impact calculation to complete.
Thus `mechanical gate: PASS` can coexist with `evidence status: UNRESOLVED`;
claim truth is not a gate condition and is not assigned by this workflow.

The expected capture digest is an explicitly supplied pipeline anchor, not an
external trusted timestamp, signature, immutable storage promise or independent
attestation. An operator able to replace both baseline and anchor is outside
this mechanical comparison. Hashes describe current bytes, not provenance truth,
package semantic correctness or an atomic multi-file snapshot.

## Local use from a reviewed source checkout

Build into a fresh directory, then run the repository's maintainer script with
the exact source version. Below, `VERSION` stands for that source version:

```bash
python -m build --no-isolation --outdir candidate .
python tools/release_evidence_preflight.py capture --root candidate --version VERSION
python tools/release_evidence_preflight.py check --root candidate --version VERSION --capture-sha256 DIGEST_FROM_CAPTURE
```

Keep the capture digest separately before checking. Check must not regenerate the
graph, recapture the receipt or derive its expected digest by rereading a possibly
changed baseline. Capture/check outputs are exclusive new files; reruns need a
fresh workspace. Reports use `researchauditkit.release-preflight/v1`, described by
`schemas/release-preflight-v1.schema.json`. The normal doctor/impact JSON remains
available alongside the gate receipt and can be displayed with `--format human`.

## Validation and boundaries

Automated tests distinguish controlled fixture faults from actual build checks.
Fixture tests inject changed bytes, missing files, changed graph/manifest, a
changed receipt and a missing expected anchor. A separate end-to-end test builds
a real wheel and source distribution, installs the wheel, verifies import
ownership and runs the gate from that installed library. No fixture bytes are
represented as valid release packages or scientific evidence.

This maintainer workflow intentionally executes the project's own build, install
and AuditKit code. It is separate from the audit library's no-target-execution
contract. CI requests only `contents: read`; it has no publishing environment,
identity-token write permission, package upload, release creation or TestPyPI
operation. Dependency bootstrap uses normal CI package infrastructure, while the
capture/check operations themselves are local. Existing publication workflows
are not changed or dispatched by this integration.
