# GitHub Action integration

The repository contains the RC3 composite Action source. GitHub Releases is the
availability authority: confirm that `v0.1.0-rc.3` exists before using the ref.
The Action is not listed in GitHub Marketplace.

## Safety contract

- runs the checked-out Action source and public `rak audit` CLI;
- audits the caller's checked-out repository without executing its code;
- provisions Action-owned Python 3.12.14 with the official SHA-pinned
  `actions/setup-python` Action;
- installs only hash-locked PyYAML 6.0.3 into an isolated runner-temporary
  virtual environment;
- loads ResearchAuditKit only from `github.action_path` under Python isolated
  mode;
- never installs target-project dependencies, metadata, or build hooks;
- requests no token and uploads no source;
- writes canonical JSON in runner temporary storage and a GitHub Job Summary;
- preserves CLI exit status;
- must be pinned to an immutable commit/tag containing `rak audit`.

Action bootstrap requires GitHub Action and Python package infrastructure. Once
bootstrap completes, `rak audit` performs repository analysis locally. No
audited repository content is uploaded, no hosted ResearchAuditKit service is
used, and target-project code is not executed.

| Bootstrap material | Exact authority |
| --- | --- |
| Python setup Action | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` (`v6`) |
| Python runtime | `3.12.14` |
| Runtime dependency | `PyYAML==6.0.3`, wheel hashes in `action/requirements.lock` |

## Versioned prerelease example

Use this only after the `v0.1.0-rc.3` GitHub prerelease is published:

```yaml
permissions:
  contents: read

steps:
  # actions/checkout v5, pinned to an immutable commit
  - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
  - uses: ernestoleo777-dotcom/ResearchAuditKit@v0.1.0-rc.3
    with:
      path: .
      fail-on: release-blocker
      output-format: human
```

Source preparation does not prove publication. Confirm the versioned tag and
prerelease on GitHub before use. Public `v0.1.0-rc.2` contains neither `rak
audit` nor `action.yml`. No mutable major/minor/latest Action alias exists; for
maximum immutability, resolve the RC3 annotated tag and pin that commit SHA.

## Inputs and outputs

Inputs are `path`, optional `policy`, `fail-on`, and `output-format`. Outputs are
canonical aggregate `status`, runner-local `result-file`, and CLI `exit-code`.
The result file is not uploaded automatically.

Local contract tests replay the trusted Action shell entry point and import
boundary. Pull-request CI invokes `action.yml` itself against PASS, WARNING,
RELEASE_BLOCKER, and ABSTAIN cases, shadow packages, customization modules,
paths with spaces, and non-execution canaries.
