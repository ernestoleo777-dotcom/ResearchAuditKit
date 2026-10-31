# Evidence Graph demo

This synthetic example belongs to the unreleased development source. Install
that reviewed source checkout using the repository quickstart before running it;
the published RC3 package does not contain `rak evidence`.

From the repository root:

```bash
python examples/evidence_graph_demo/run_demo.py
```

The script invokes the installed CLI in six temporary fixture copies, checks
exit codes and JSON results, prints one compact JSON summary, and removes only
its own temporary files. It leaves these shipped fixtures unchanged.

| Case | Command | Exit | Result | Artifact observation |
| --- | --- | --- | --- | --- |
| validate | `evidence validate` | 0 | PASS | Not read |
| matched | `evidence doctor` | 2 | UNRESOLVED | MECHANICALLY_VERIFIED |
| changed | `evidence doctor` | 1 | INVALID | IDENTITY_MISMATCH |
| missing | `evidence doctor` | 2 | UNRESOLVED | MISSING |
| impact-changed | `evidence impact` | 1 | INVALID | IDENTITY_MISMATCH |
| impact-missing | `evidence impact` | 2 | UNRESOLVED | MISSING |

The matched case intentionally remains UNRESOLVED: the declared Claim has
`resolution: UNRESOLVED`. The file digest matches, while the tool makes no
scientific judgment about that claim. Structural validation does not read the
artifact and does not establish that it exists.

To inspect declared provenance directly:

```bash
rak evidence trace urn:rak:demo:claim:statement@1 --graph examples/evidence_graph_demo/graph.json
```

The expected exit is 2 and the report includes Claim, Evidence and Artifact.
`source_refs` and SUPPORTS are declarations supplied by the example author;
they are not inferred from the record's text. This synthetic example is not a
real-consumer acceptance result or a substitute for separately approved evidence.

The two impact cases additionally print the affected claim ID and the declared
Artifact → Evidence → Claim witness path. Changed stable bytes are a confirmed
identity mismatch; a missing file leaves identity unresolved. These paths say
which supplied declarations require review, not whether the claim is false.
