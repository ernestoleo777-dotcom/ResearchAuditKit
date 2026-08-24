# Quickstart

This walkthrough starts from a clean clone, installs the development version, and
runs a synthetic PASS plus an intentionally detected repository problem. It does
not require a GPU, model API, secret, or research dataset.

## 1. Clone and create an environment

```bash
git clone https://github.com/ernestoleo777-dotcom/ResearchAuditKit.git
cd ResearchAuditKit
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and replace the
POSIX temporary-directory commands below with paths under `$env:TEMP`.

The supported evaluation path is installation from a source checkout. No stable
PyPI release is claimed. Installation may access the configured package source to
resolve PyYAML; audit commands make no runtime network calls.

## 2. Inspect the installed CLI

```bash
rak --version
rak --help
rak inventory --help
```

The expected source version is `0.1.0rc2`. This release candidate is not yet
tagged or published.

## 3. Run the synthetic demo

```bash
export RAK_DEMO_ROOT="$(mktemp -d)"
set -e
rak inventory --root examples/repository_integrity_demo/pass_repo --policy examples/repository_integrity_demo/policy.yaml --out "$RAK_DEMO_ROOT/pass"
set +e
rak inventory --root examples/repository_integrity_demo/issue_repo --policy examples/repository_integrity_demo/policy.yaml --out "$RAK_DEMO_ROOT/issue"
RAK_ISSUE_CODE=$?
set -e
test "$RAK_ISSUE_CODE" -eq 2
```

The first command returns 0. The second returns 2 because `policy.yaml` requires a
repository-root `README.md` and `issue_repo` intentionally omits it. The nonzero
code is an expected audit result in this example, not a crash.

## 4. Inspect and interpret output

```bash
python -m json.tool "$RAK_DEMO_ROOT/pass/summary.json"
python -m json.tool "$RAK_DEMO_ROOT/issue/summary.json"
python -m json.tool "$RAK_DEMO_ROOT/issue/inventory.json"
```

The stable summaries should match
[`expected/pass_summary.json`](../examples/repository_integrity_demo/expected/pass_summary.json)
and
[`expected/issue_summary.json`](../examples/repository_integrity_demo/expected/issue_summary.json).
The issue inventory contains a `README.md` row with gate status
`MISSING_REQUIRED`.

Inventory rows also contain file modification times, sizes, and SHA-256 hashes.
Those fields legitimately depend on checkout metadata and file content; the demo
does not claim byte-identical inventories across filesystems.

## 5. Understand exit status

- `0`: the command completed and no failing mechanical gate applied.
- `2`: a configured mechanical failure, invalid input, or handled operational
  error occurred.

Some report-only commands always return 0 for valid input even when their output
contains descriptive findings. Consult the [command reference](command_reference.md)
before using a command as a CI gate.

The demo establishes only that the supplied policy detected a missing required
file. It says nothing about scientific validity or the quality of a project.
