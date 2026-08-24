# CI Integration

The following GitHub Actions workflow installs from the checked-out source and
runs the same synthetic PASS/finding demo as the README. It uses real `rak`
commands, needs no secret, and does not reference an unpublished package index.

```yaml
name: ResearchAuditKit preflight

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  repository-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install from this checkout
        run: python -m pip install -e .
      - name: Run synthetic repository preflight
        shell: bash
        run: |
          set -euo pipefail
          output_dir="$(mktemp -d)"
          rak inventory \
            --root examples/repository_integrity_demo/pass_repo \
            --policy examples/repository_integrity_demo/policy.yaml \
            --out "$output_dir/pass"
          set +e
          rak inventory \
            --root examples/repository_integrity_demo/issue_repo \
            --policy examples/repository_integrity_demo/policy.yaml \
            --out "$output_dir/issue"
          issue_code=$?
          set -e
          test "$issue_code" -eq 2
          python -m json.tool "$output_dir/pass/summary.json"
          python -m json.tool "$output_dir/issue/summary.json"
```

The job passes only when the complete fixture returns 0 and the intentionally
incomplete fixture returns 2. Replace the synthetic roots and policy with your own
repository paths only after reviewing the [command reference](command_reference.md)
and [limitations](limitations.md).

Do not treat every report-only command as a CI gate: `support-audit`,
`pareto-audit`, `evidence-index`, and `claims evaluate` return 0 for valid reports
and communicate findings in their output. Select commands and status fields that
match the intended mechanical contract.
