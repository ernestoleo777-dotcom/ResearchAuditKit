# GitHub Action integration

The repository contains an unpublished composite Action for owner review. It is source-prepared, not tagged, released, or listed in GitHub Marketplace.

## Safety contract

- runs the checked-out Action source and public `rak audit` CLI;
- audits the caller's checked-out repository without executing its code;
- performs no dependency installation or network call;
- requests no token and uploads no source;
- writes canonical JSON in runner temporary storage and a GitHub Job Summary;
- preserves CLI exit status;
- requires Python 3.10+ and PyYAML 6+ already available;
- must be pinned to an immutable commit/tag containing `rak audit`.

## Publication-gated example

Do not copy this placeholder until the owner publishes an immutable ref containing the reviewed vertical slice:

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.12"
  - name: Verify runtime prerequisite
    run: python -c 'import yaml; assert int(yaml.__version__.split(".")[0]) >= 6'
  - uses: ernestoleo777-dotcom/ResearchAuditKit@<IMMUTABLE_REF_CONTAINING_AUDIT>
    with:
      path: .
      fail-on: release-blocker
      output-format: human
```

The Action intentionally does not install a mutable dependency or target-project requirements. Publication therefore depends on an owner-reviewed immutable ResearchAuditKit source/release ref and an explicitly provisioned Python/PyYAML environment.

## Inputs and outputs

Inputs are `path`, optional `policy`, `fail-on`, and `output-format`. Outputs are canonical aggregate `status` and runner-local `result-file`. The result file is not uploaded automatically.

Local contract tests replay the actual Action shell entry point against PASS, WARNING, and RELEASE_BLOCKER fixtures and validate Job Summary escaping.
