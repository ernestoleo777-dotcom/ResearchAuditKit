# ResearchAuditKit

> A lightweight toolkit for auditing scientific repository integrity, data support, experiment isolation, and evidence-backed research decisions.

ResearchAuditKit checks the mechanics of a scientific evidence chain: which files were governed, whether declared files changed, where candidate coordinates sit relative to observed support, whether result tables contain unsupported selections, whether split metadata indicates leakage, and whether declared gates were followed.

## What it does not do

The toolkit does not decide that a scientific conclusion is correct. It does not replace domain experts, experimental truth, or peer review. A joint-support failure is not evidence of physical impossibility. Matching hashes establish byte identity, not scientific validity. A gate `PASS` means only that the configured protocol criteria passed; it says nothing about venue acceptance.

## Install

From a source checkout:

```bash
python -m pip install -e .
```

For a built wheel:

```bash
python -m pip install dist/research_audit_kit-0.1.0-py3-none-any.whl
```

Python 3.10+ and PyYAML are required. Installation may resolve PyYAML from the configured package source; runtime commands themselves make no network calls. The quickstart below assumes a source checkout because it uses the repository's example files.

## Five-minute quickstart

```bash
rak inventory --root examples/integrity_demo --policy configs/integrity_policy.example.yaml --out /tmp/rak-inventory
rak freeze --root examples/integrity_demo --policy configs/integrity_policy.example.yaml --baseline /tmp/demo-baseline.csv
rak verify --root examples/integrity_demo --baseline /tmp/demo-baseline.csv --out /tmp/rak-verify
rak support-audit --data examples/conditional_support_demo/data.csv --features architecture,optimizer,momentum,depth --discrete architecture,optimizer,momentum,depth --schema configs/support_schema.example.yaml --out /tmp/rak-support
```

## CLI

```text
rak init --root REPO --policy POLICY
rak inventory --root REPO --policy POLICY --out DIR
rak freeze --root REPO --policy POLICY --baseline FILE [--force]
rak verify --root REPO --baseline FILE --out DIR
rak support-audit --data CSV --features a,b --discrete a,b --out DIR
rak pareto-audit --candidates CSV --objectives loss:min,cost:min --support-column support_status --out DIR
rak split-audit --data CSV --manifest CSV --id-column row_id --out DIR
rak gate --metrics JSON --policy YAML --out DIR
rak deviation record --config YAML --out LEDGER.csv
rak claims evaluate --claims CSV --evidence CSV --out DIR
```

Every command has `--help`, emits a machine-readable summary, and returns a nonzero code for invalid input or a failed scientific gate. Warnings do not fail a command. Baselines are never overwritten unless `--force` is supplied; forced replacement is recorded.

## Output example

```json
{
  "command": "verify",
  "gate_status": "PASS",
  "counts": {"MATCH": 2}
}
```

## Limits and claim boundary

- Empirical support is a property of supplied data and rules, not a physical law.
- Support-contamination metrics do not measure true objective error.
- Leakage checks based only on metadata can return `UNVERIFIED_FROM_METADATA`.
- User policies determine what is included and what causes failure.
- Passing a configured gate does not guarantee that all leakage has been detected.
- The toolkit does not guarantee scientific conclusions, physical feasibility, or paper acceptance.
- Negative results are preserved as evidence; `FAIL` is not automatically a software defect.
- Non-baseline report files are atomically replaced when a command is rerun against the same output directory. Baselines are the exception: they refuse overwrite unless `--force` is explicit, and the forced action is recorded in the baseline.

See `docs/limitations.md` for the complete boundary.

## Data privacy

Commands operate on local paths. The package performs no network calls and ships only newly authored synthetic fixtures. Inventory and manifest outputs may reveal filenames and hashes; review them before sharing.

## License

Licensed under the Apache License, Version 2.0. See the repository-root [LICENSE](LICENSE) file for the complete terms.

## Project status

Release-candidate engineering tool licensed under Apache-2.0. No public remote or release has been created yet. It is a reproducibility utility, not a research project, dataset, benchmark, or paper artifact; see `LICENSE_STATUS.md`.
