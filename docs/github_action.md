# GitHub Action integration

The repository contains an unpublished composite Action for owner review. It is source-prepared, not tagged, released, or listed in GitHub Marketplace.

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

## Publication-gated example

Do not copy this placeholder until the owner publishes an immutable ref containing the reviewed vertical slice:

```yaml
permissions:
  contents: read

steps:
  # actions/checkout v5, pinned to an immutable commit
  - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
  - uses: ernestoleo777-dotcom/ResearchAuditKit@<IMMUTABLE_REF_CONTAINING_AUDIT>
    with:
      path: .
      fail-on: release-blocker
      output-format: human
```

The placeholder is future-form only. Public `v0.1.0-rc.2` contains neither
`rak audit` nor `action.yml`; `v0.1.0-rc.3` does not yet exist. A separately
authorized RC3 release must supply the immutable ResearchAuditKit ref before
consumers can use this interface.

## Inputs and outputs

Inputs are `path`, optional `policy`, `fail-on`, and `output-format`. Outputs are
canonical aggregate `status`, runner-local `result-file`, and CLI `exit-code`.
The result file is not uploaded automatically.

Local contract tests replay the trusted Action shell entry point and import
boundary. Pull-request CI invokes `action.yml` itself against PASS, WARNING,
RELEASE_BLOCKER, and ABSTAIN cases, shadow packages, customization modules,
paths with spaces, and non-execution canaries.
