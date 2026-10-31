# Start an evidence graph from an asset list

These commands are unreleased development functionality in the reviewed source
checkout. Published RC3 packages do not contain them. Use the source installation
instructions in the repository quickstart.

## 1. List the assets you intend to include

Create `assets.json` in your project directory:

```json
{
  "schema": "researchauditkit.asset-list/v1",
  "assets": [
    {"name": "results", "path": "results.csv"}
  ]
}
```

The named file is an example; replace it with your own explicit relative path.
The list is input data, never executable instructions. There is no repository
scan, file discovery or inference from prose. Names use letters/digits followed
by up to 127 letters/digits, dots, underscores or hyphens. Names and asset paths
must be unique. An optional `media_type` defaults to `application/octet-stream`.

Claims are optional. Add them only with your own statement and explicit asset
names for support or contradiction:

```json
"claims": [
  {
    "name": "main",
    "statement": "Your explicitly declared claim",
    "supports": ["results"],
    "contradicts": []
  }
]
```

This is a fragment to insert as a top-level field in the asset-list document.
These links are your declarations; the tool does not determine whether an asset
supports or contradicts the statement. A claim without links remains unlinked.
The complete [synthetic template](../examples/evidence_graph_demo/assets.json)
is included in the source distribution. The asset-list schema is
`schemas/evidence-assets-v1.schema.json`.

## 2. Generate the graph

From your project directory:

```bash
rak evidence init --manifest assets.json --out graph.json --namespace my-project
```

`--namespace` defaults to `project`; `--version` defaults to the explicit initial
version `1`. Floating version names are rejected. `--root` defaults to the
manifest directory and confines both assets and output. The output parent must
already exist. Existing outputs, inputs and escaping paths are never replaced.

The initializer creates one Artifact and one Evidence per listed asset, plus
only the Claims and SUPPORTS/CONTRADICTS links you explicitly supplied. IDs are
generated deterministically; all assertion levels are DECLARED and every Claim
remains UNRESOLVED. Hashes capture current stable file bytes, not historical
authenticity or verification against an independent expected digest.

Missing, unreadable, nonlocal or budget-limited assets retain unresolved reasons
without an invented hash. Their graph can still be created, with exit 2. Unsafe
paths, linked/nonregular inputs, invalid declarations or output collisions return
1 without publishing a graph. Normal creation returns 0, even with unresolved
Claim declarations: creation is not claim adjudication. The receipt explicitly
states whether an output was created; inspect that flag after a failure.

The same existing graph, node, edge and artifact-read budgets apply. All asset
paths, references and identity fields are validated before any asset is opened.
A generated graph must also fit the graph read budget. On macOS the no-download
policy covers reads and its restoration must succeed before graph publication.
No model, network, execution, implicit hydration or automatic experiment rerun
is introduced. These observations do not form an atomic multi-file snapshot.

Initialization defaults to a human-readable receipt. Use `--format json` for the
`researchauditkit.evidence-init/v1` receipt (`schemas/evidence-init-v1.schema.json`).
The `--out` file is the generated evidence/v1 graph, not that receipt.

## 3. Read the impact report

```bash
rak evidence impact graph.json --format human --out impact.json
```

The terminal report shows problem file, claim to review, current/historical
witness paths and review items. A stable byte mismatch is distinguished from
missing/unresolved identity. Analysis marked INCOMPLETE/NOT_ANALYZED must not be
read as a complete list of affected claims. Not-reached claims are not certified
unaffected. Matching files do not resolve declared claim truth.

`--format human` also works with validate, trace and doctor. Those four existing
commands retain JSON as their default. Formatting changes stdout only: `--out`
still stores the same canonical JSON result, and exit codes remain unchanged.
Human text escapes terminal controls and direction-changing characters. Values
longer than 512 characters, lines longer than 2,000 characters and reports beyond
400 lines are explicitly truncated; use JSON for full details.

## Replay the complete synthetic workflow

```bash
python examples/evidence_graph_demo/run_onboarding.py
```

This creates a graph from the supplied template, changes its own temporary
artifact copy, and displays the resulting impact path and review items. It
preserves the shipped files and removes only its own temporary directory. It is
an engineering demonstration, not real-consumer or scientific acceptance evidence.
