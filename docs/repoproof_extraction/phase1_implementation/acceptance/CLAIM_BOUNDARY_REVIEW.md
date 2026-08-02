# Claim-boundary review

## Red-team prompts checked

The review tested whether a successful command could be interpreted as a
correct prediction, independent authorship, trusted timing, human separation,
absence of copies, access control, evidence truth, or claim support. None of
those interpretations is endorsed by the CLI summaries, custody documentation,
or module limitations.

## Result

- Prediction seal and verify: PASS only for supplied declaration consistency.
  They do not compare an outcome, compute a score, establish independent
  authorship, or establish trusted time ordering.
- Isolation audit: PASS only for declared local structural policy. It does not
  enforce operating-system permissions or establish human separation, no prior
  access, no hidden copies, or blinding.
- Evidence index: PASS only for well-formed, role-labelled supplied metadata.
  It does not read evidence content, adjudicate a claim, verify provenance, or
  establish scientific truth.

Result: `CLAIM_BOUNDARY_PASS`.
