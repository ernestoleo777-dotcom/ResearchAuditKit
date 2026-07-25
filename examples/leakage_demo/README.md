# Leakage Demo

This fixture intentionally contains group overlap, so the command is expected to return a nonzero code:

```bash
rak split-audit --data examples/leakage_demo/data.csv --manifest examples/leakage_demo/manifest.csv --id-column row_id --group-column dataset_group --time-column timestamp --out /tmp/rak-leakage-demo
```

