# Evidence Graph B1

This local development feature is additive to `researchauditkit.audit/v1`; it does not change
audit/freeze/verify/gate exit meanings or publish a release.

## Start with a synthetic example

[Run the public CLI demo](../examples/evidence_graph_demo/README.md) to compare
structural validation, matching bytes, a changed file and a missing file. The
matched-file case retains an unresolved Claim rather than assigning its truth.

## Document and identity

The JSON document has exactly `schema: researchauditkit.evidence/v1`, `nodes`, and `edges`.
See `schemas/evidence-v1.schema.json` for the document and result envelopes. Nodes are Claim,
Evidence, ExperimentRun, Artifact, Protocol and Decision. Every node declares a `logical_id`
(`urn:rak:NAMESPACE:type-lowercase:NAME`), a nonfloating explicit `version`, exact
`id = logical_id@version`, and `assertion_level`. IDs are never silently updated after a hash mismatch.
An Artifact declares a relative `path`, `media_type`, and SHA-256 or `unresolved_reason`.
Evidence `source_refs`, Protocol `artifact_refs`, Run `protocol_ref`/`record_refs`, and
Decision `external_adjudication_ref` are typed node IDs, not executable instructions or file URLs.

## Relationships and uncertainty

The five relations are SUPPORTS, CONTRADICTS, DERIVED_FROM, SUPERSEDES, and DEPENDS_ON.
The validator enforces typed endpoints and exact references. Combined DERIVED_FROM/DEPENDS_ON
and explicit typed provenance references form an acyclic dependency graph. SUPERSEDES is
separately acyclic, within one type/logical ID and across distinct versions. Multiple current
heads remain VERSION_FORK_UNRESOLVED. Reciprocal contradictions are legal and traversal is bounded.

Trace follows incoming support/contradiction of claims and outgoing explicit dependencies,
provenance references and contradictions. Graph-wide version-health findings remain visible
even outside a claim's traversal. It does not infer relationships from prose.
`citation_context: historical` records an intentionally retained citation to superseded evidence.
Current citations are flagged stale; supersession never invalidates a past experiment by itself.

Claim resolutions are ABSTAIN, UNRESOLVED or EXTERNAL_ADJUDICATION_RECORDED. Decision outcomes
are GO, NO_GO, ABSTAIN or UNRESOLVED. These declarations are preserved, never assigned as a
scientific verdict by this tool. Input MECHANICALLY_VERIFIED is a declaration; only artifact
observations can acquire that status after a stable local SHA-256 match. An external adjudication
record supplies `identity`, `method`, `scope`, and an Artifact `record_ref`; even a complete
record is reported as externally supplied and is not scientifically validated.

## Filesystem and resource scope

`--root` defaults to the graph's directory. Artifact paths are canonical relative paths.
Absolute, parent traversal, drive, UNC, backslash, control-character, symlink and nonregular
paths are rejected. Descriptor-bound parent/root checks detect replacement races; inode, size,
mode and nanosecond time checks surround reads. Hard-linked input files are rejected.
Missing, unreadable or dataless inputs are explicit unresolved states. On macOS the current
thread disables implicit File Provider hydration and restores its previous policy afterward.
There is no network, subprocess, model, unpickling, automatic repository scan, or source rewrite.

Defaults: 2 MiB graph, 2,048 nodes, 8,192 edges, depth 64, 64 MiB per artifact and 256 MiB
aggregate artifact reads. Duplicate JSON keys, nonfinite numbers, oversized integers and
excessive nesting are rejected. Library callers may pass an explicit positive `Limits` budget.
Validation is structural and does not read artifact contents. Trace/doctor observe only declared
Artifact nodes. A budget-limited artifact remains unresolved.

`--out` opts into one new report within the root, with an existing safe parent directory.
The complete report is atomically published with an exclusive name; no existing file is replaced.
Only the operation's own temporary output may be cleaned up.

## Results and exits

Results contain sorted nodes, edges, findings, explicit reference paths and artifact observations.
`graph_content_sha256` canonicalizes graph order and reference lists. `result_content_sha256`
contains portable declared paths and observed byte identities; host paths, inodes, and generated
times are excluded. Inodes/times are used for local stability checks, not as historical proof.
Exit 0 means mechanical checks complete in the command's scope; 1 means invalid graph/path or
a definite identity failure; 2 means required evidence is unresolved or explicitly ABSTAIN/UNRESOLVED.
No exit code proves a scientific claim.

## Tests and private real demo

`tests/test_evidence_graph_b1.py` maps EG01–EG25 to the B0 specification. EG25 requires an explicitly
approved real receipt directory through `RAK_EVIDENCE_APPROVED_DEMO_ROOT`; absent that scope it
skips, rather than substituting synthetic data. The V4.3 execution uses its own directory
acceptance receipts in a private SSD report directory. No frozen research conclusions are
imported into this product repository.

## Engineering closure safeguards

Typed provenance references from current nodes to superseded targets are stale-current findings;
references originating in superseded nodes remain explicitly historical. File mount boundaries
are checked before opening a leaf. Aggregate artifact budgets debit bytes even when a later
identity check rejects that read; growth detection uses final descriptor metadata without an
extra byte beyond the budget. Reports include `scope_limits.artifact_bytes_read`.

The no-download policy is installed before root resolution. Restoration is verified before a
requested report is published; restoration failure remains UNRESOLVED and does not publish a
success-shaped output. Five additional engineering regression tests retain the original B0
25-case contract without weakening its assertions.

## Artifact impact analysis (development)

`rak evidence impact GRAPH.json` performs the same bounded artifact observations
as `doctor`, then propagates identity issues through explicitly declared links.
It accepts the same `--root` and new-file-only `--out` options. Existing command
results and exit meanings are unchanged. The result retains the evidence/v1
envelope and adds `impact_analysis`, described by
`schemas/evidence-impact-v1.schema.json`.

A stable digest mismatch starts a CONFIRMED identity-change record. Missing,
unreadable, unsafe, unidentifiable or budget-limited artifacts start UNRESOLVED
identity records. Matching artifacts do not start impact records; a declaration
may still be unresolved in the overall result. There is no automatic rescan of
undeclared files, code execution, experiment rerun, or relationship inference.

Propagation reverses DERIVED_FROM/DEPENDS_ON and typed provenance references,
and follows SUPPORTS/CONTRADICTS toward their targets. SUPERSEDES is not a
propagation link: an older file's issue does not by itself implicate its newer
version. Graph-wide forks, stale citations and other health findings remain
visible. NOT_SUPERSEDED means only that no supplied SUPERSEDES edge targets that
claim version; it does not select a winner in a version fork.

Each record lists reached node IDs, potentially affected claim IDs, and one
deterministic shortest witness per artifact/claim/current-or-historical context.
The witness contains node IDs and a relation/typed-reference field for each hop.
Alternative paths in the same context are not enumerated. Any explicit historical
citation or superseded node makes that path historical; both contexts remain
visible when both exist. Contradiction cycles terminate without deciding truth.

`analysis_status` is COMPLETE only when propagation completes within its budget,
INCOMPLETE when any summary/traversal bound is exhausted, and NOT_ANALYZED when
the input cannot be validated/read. These refer to impact computation, not claim
truth or complete evidence. Defaults allow 8,192 propagation steps, 8,192 total
witness hops, 2,048 claim paths and depth 64, derived from Limits.edges/nodes/depth.
Usage is included. An exhausted budget adds an explicit unresolved finding; no
truncation is silently reported as complete. `not_reached_claim_ids` means only
that no examined declared route reached those claims. It is not proof that they
are unaffected, especially for an incomplete graph or analysis.

The graph and result digests remain deterministic. Existing read, no-download,
exclusive-publication and input-preservation safeguards also apply to impact.
