# Limitations

ResearchAuditKit performs mechanical verification against supplied files, metadata,
and policies. Its results are deliberately narrower than scientific review.

## Interpretation boundary

- Policies are user-authored and can omit important assets or choose weak rules.
- Hashes establish byte identity only, not semantic correctness or authorship.
- Empirical support is a property of supplied data/rules, not a physical or causal
  property.
- Pareto audits trust supplied objectives, directions, values, and labels; they do
  not validate response truth or real-world performance.
- Metadata-only leakage analysis cannot observe undocumented preprocessing,
  duplication, access, or communication.
- A configured gate can be evaluated correctly even when its threshold is poorly
  chosen.
- A local PASS does not guarantee reproducibility, scientific validity, claim
  truth, causal validity, novelty, project quality, publication merit, or
  acceptance.

## Custody and authority boundary

- Prediction seals establish supplied-byte consistency only. They do not establish
  trusted timing, independent authorship, prediction correctness, or outcome
  unavailability.
- Workspace isolation is structural. It cannot establish human separation,
  permissions, access-control enforcement, process history, or absence of copies.
- Evidence indexes record asserted custody metadata without adjudicating evidence
  or validating a claim.
- Local records have no external timestamp or authority unless a user separately
  supplies and verifies one; the current CLI provides no such integration.

## Platform and filesystem boundary

- Package metadata supports Python 3.10 or newer; repository CI covers 3.10–3.12.
- The documented quickstart uses POSIX shell syntax. CLI paths are Python paths,
  but Windows activation and temporary-directory commands differ.
- Permissions, unavailable files, invalid Unicode, unsupported special filesystem
  objects, and escaping symlinks can stop an audit with exit code 2.
- Inventory records checkout/filesystem modification times. Baselines also contain
  creation time, generated identifier, root-directory name, and content digest.
  Do not expect byte-identical outputs when those inputs differ.
- Case-insensitive path collisions are rejected to protect portable interpretation.

## Input and execution boundary

- Commands accept only their documented JSON, YAML, and CSV contracts. Some closed
  JSON contracts reject unknown fields and duplicate keys; other general inputs
  follow their command-specific parser.
- ResearchAuditKit does not deserialize model objects, run notebooks, import audited
  code, train models, call model APIs, or inspect remote repositories.
- The package cannot replace domain review, replication, security review, privacy
  review, peer review, or publication assessment.

## Output boundary

- Report files can reveal repository paths, filenames, sizes, hashes, and supplied
  metadata. Review them before sharing.
- Ordinary report files are replaced on rerun. Baselines and prediction seals are
  protected against overwrite by default, but explicit `--force` can replace them
  and is recorded.
- Exit code 2 combines detected mechanical failures, invalid input, and handled
  operational errors. Read the JSON summary/stderr rather than interpreting the
  code alone.
