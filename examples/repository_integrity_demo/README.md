# Repository Integrity Demo

This Apache-2.0-licensed synthetic example uses the real `rak inventory` command.
`pass_repo` contains every file required by `policy.yaml`. `issue_repo`
intentionally omits `README.md`, so the command records `MISSING_REQUIRED` and
returns exit code 2.

From an installed source checkout:

```bash
export RAK_DEMO_ROOT="$(mktemp -d)"
set -e
rak inventory --root examples/repository_integrity_demo/pass_repo --policy examples/repository_integrity_demo/policy.yaml --out "$RAK_DEMO_ROOT/pass"
set +e
rak inventory --root examples/repository_integrity_demo/issue_repo --policy examples/repository_integrity_demo/policy.yaml --out "$RAK_DEMO_ROOT/issue"
RAK_ISSUE_CODE=$?
set -e
test "$RAK_ISSUE_CODE" -eq 2
python -m json.tool "$RAK_DEMO_ROOT/pass/summary.json"
python -m json.tool "$RAK_DEMO_ROOT/issue/summary.json"
```

The expected status/count projections are stored in `expected/`. Inventory rows
also contain checkout-dependent modification times, sizes, and content hashes, so
the demo compares the stable summary rather than claiming byte-identical reports.
The detected omission is a repository-policy failure, not a scientific judgment.
