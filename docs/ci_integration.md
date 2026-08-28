# CI integration

## Prepared composite Action

The preferred post-publication interface is an immutable Action ref:

```yaml
name: ResearchAuditKit preflight

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  repository-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Verify pre-provisioned runtime
        run: python -c 'import yaml; assert int(yaml.__version__.split(".")[0]) >= 6'
      - uses: ernestoleo777-dotcom/ResearchAuditKit@<IMMUTABLE_REF_CONTAINING_AUDIT>
        with:
          path: .
          fail-on: release-blocker
          output-format: human
```

The placeholder is intentionally not a working publication instruction. The current public RC2 artifact does not contain `rak audit`, and this task creates no tag or release. Replace it only after owner review and an immutable publication decision.

The composite Action installs nothing, requests no token, uploads nothing, executes no target-project code, and preserves the CLI exit code. It writes canonical JSON under runner temporary storage and renders non-PASS findings into GitHub Job Summary. Python 3.10+ and PyYAML 6+ must already be provisioned by the caller.

## Source-checkout CI before publication

For branch review, install the checked-out source and invoke the same CLI directly:

```yaml
name: ResearchAuditKit branch review

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  repository-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install this review checkout
        run: python -m pip install -e .
      - name: Audit repository
        run: rak audit . --format json --output "$RUNNER_TEMP/rak-audit.json"
```

This source-checkout workflow applies to ResearchAuditKit's own review branch. A consumer must not substitute an unpinned branch for the required immutable Action ref.

## Exit policy

The default fails on `RELEASE_BLOCKER` and `ABSTAIN/UNRESOLVED`; warnings remain visible but do not fail. Set `fail-on: warning` only when the repository owner has deliberately chosen that stricter policy. A Job Summary is an interface, not a certification badge.

Advanced report-only commands retain their documented behavior and are not invoked by the Action. See the [command reference](command_reference.md) before composing additional CI gates.
