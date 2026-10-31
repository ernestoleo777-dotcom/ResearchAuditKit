# Gate an explicit evidence baseline in a project

This is unreleased development functionality. Install the reviewed source checkout
as described in the quickstart; published RC3 packages do not contain this command.

`rak evidence check` applies a narrow mechanical policy to the same bounded,
confined impact calculation. It checks every Artifact in the graph, including
historical versions. It neither runs project code nor searches for new assets.
Use a separate explicitly scoped graph when historical artifacts are unavailable;
do not remove declarations merely to obtain a passing result.

## Capture once, retain the anchor, check later

Initialize the graph from your explicit asset list:

```bash
rak evidence init --manifest assets.json --out graph.json --namespace my-project --format json
```

Save the initialization receipt's **graph_content_sha256** separately, for example
in the CI configuration approved with the baseline. It is the normalized graph
content digest, not the raw file hash: whitespace and collection order do not
change it, while declarations, paths, versions, identities and links do.
Never regenerate the baseline or derive the expected digest from the graph being
checked in the same check job. Review any intended baseline and anchor update.

Check against that saved value, replacing `SAVED_GRAPH_CONTENT_SHA256` below:

```bash
rak evidence check graph.json --graph-sha256 SAVED_GRAPH_CONTENT_SHA256 --format human --out check.json
```

A matching baseline and all matching artifact identities are necessary. The gate
also requires at least one Artifact, complete impact analysis and no INVALID or
UNRESOLVED finding. INFO observations are retained and do not block. The graph
anchor is checked before artifact reads; a mismatching anchor stops analysis.

An explicitly declared unresolved Claim normally blocks the gate. If your
mechanical CI policy allows a particular claim to remain unadjudicated, add its
exact versioned ID:

```bash
rak evidence check graph.json --graph-sha256 SAVED_GRAPH_CONTENT_SHA256 --allow-unresolved-claim urn:rak:my-project:claim:main@1 --out check.json
```

Repeat the option for each explicitly accepted Claim. There is no wildcard,
blanket unresolved allowance or automatic acceptance. Unknown, duplicate,
non-Claim or non-UNRESOLVED IDs are invalid. Acceptance covers only that Claim's
`EXPLICIT_UNRESOLVED` finding. Missing evidence chains, contradictory declarations,
version forks, stale references, missing identities, ABSTAIN decisions, unavailable
files, unsafe paths, read limits and incomplete propagation still block.

## CI and report contract

Use the same check command in a CI shell step after installing your reviewed
AuditKit revision. An exit of **0** means the mechanical policy passed; **1**
means invalid input, definite mismatch or unsafe access; **2** means unresolved
requirements. Both 1 and 2 fail a normal CI step. Keep the baseline and anchor
under the project's review controls. This command does not install dependencies,
run experiments, refresh hashes, download cloud placeholders or publish artifacts.

JSON is the default; `--format human` changes stdout only. `--out` publishes the
same JSON to a new file inside the root (default: graph directory). Existing
outputs and graph/artifact paths cannot be overwritten, including missing
artifact paths. Failures before safe output preparation may produce stdout only;
consume the exit code and do not assume an output file exists after failure.

The `researchauditkit.evidence-check/v1` receipt contains `mechanical_gate`,
`status`, the original `evidence_status`, exact accepted findings, blocking findings,
and the complete original impact report in `evidence_result`. A mechanical PASS
may coexist with evidence UNRESOLVED; no node or claim is changed or adjudicated.
Human failures show the original problem files and declared claim paths.

This anchor is supplied by the caller. Someone able to replace both graph and
anchor can authorize a different baseline. It is not a signature, independent
attestation, trusted timestamp, scientific acceptance or atomic multi-file snapshot.
A passing check covers only the explicitly listed files and declarations, not
unlisted inputs or project reproducibility. This feature adds no consumer count.
