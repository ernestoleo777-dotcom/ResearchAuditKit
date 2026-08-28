# Quickstart

This walkthrough exercises the unpublished owner-review source checkout. The current public RC2 artifact does not contain `rak audit`; no publication is claimed.

## Install the checkout

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Python 3.10–3.12 is the supported CI matrix. Installation may resolve PyYAML from the configured package source; audit execution itself is offline and local.

## Audit the current repository

```bash
rak --version
rak audit .
```

No configuration is required. The command applies the built-in policy and reports whether `.rak/policy.yaml` was available.

## Replay PASS, WARNING, and RELEASE_BLOCKER

```bash
rak audit examples/audit_demo/pass_repo
rak audit examples/audit_demo/warning_repo
set +e
rak audit examples/audit_demo/blocker_repo
blocker_code=$?
set -e
test "$blocker_code" -eq 2
```

The blocker fixture's `.rak/policy.yaml` requires `artifacts/model.bin`, which is intentionally absent. The warning fixture omits a license but returns 0 under the default threshold.

## Write canonical JSON

```bash
output_dir="$(mktemp -d)"
rak audit examples/audit_demo/pass_repo --format json --output "$output_dir/audit.json"
python -m json.tool "$output_dir/audit.json"
```

The result conforms to [`researchauditkit.audit/v1`](../schemas/audit-result-v1.schema.json). It contains no timestamp or absolute target path, so reruns over the same paths, bytes, and policy are stable.

## Continue through the lifecycle

After reviewing the audit, use a deliberate project policy with `rak freeze`, preserve the baseline, run `rak verify` against later states, and apply `rak gate` only when a separately authored metrics/gate contract exists. See the [workflow guide](research_release_workflow.md).
