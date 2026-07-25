# Conditional Support Demo

Run from the repository root:

```bash
rak support-audit --data examples/conditional_support_demo/data.csv --features architecture,optimizer,momentum,depth --discrete architecture,optimizer,momentum,depth --schema configs/support_schema.example.yaml --out /tmp/rak-support-demo
```

The output reports empirical support only. It does not interpret real-world feasibility.

