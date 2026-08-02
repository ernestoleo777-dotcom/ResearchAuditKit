# Custody Demo

These files are synthetic, generic command inputs for local smoke testing.

```bash
rak prediction-seal --input examples/custody_demo/declaration.json --out /tmp/rak-demo-seal.json
rak prediction-verify --input examples/custody_demo/declaration.json --seal /tmp/rak-demo-seal.json --out /tmp/rak-demo-verify
rak isolation-audit --root examples/custody_demo/workspaces --manifest examples/custody_demo/workspaces.json --out /tmp/rak-demo-isolation
rak evidence-index --roles examples/custody_demo/roles.json --records examples/custody_demo/records.json --out /tmp/rak-demo-evidence
```

Passing commands establish only their documented local custody contracts. They do not establish scientific correctness, trusted time ordering, role separation, or claim validity.
