# Pareto Audit Demo

Run from the repository root:

```bash
rak pareto-audit --candidates examples/pareto_audit_demo/candidates.csv --objectives loss:min,latency:min --support-column support_status --selected-column selected --claimed-column claimed --out /tmp/rak-pareto-demo
```

The reported contamination metrics concern supplied support labels, not objective truth.

