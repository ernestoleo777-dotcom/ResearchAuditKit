# Documentation Execution Report

## README

The editable installation command was executed in an independent temporary environment without network access. The four five-minute quickstart commands were then executed from a source checkout with only output destinations redirected to isolated temporary paths.

| Documented flow | Result | Observed contract |
| --- | --- | --- |
| inventory | PASS | 2 assets, status `PASS` |
| freeze | PASS | 2 governed assets; baseline plus companion hash |
| verify | PASS | `counts={"MATCH": 2}`, gate `PASS` |
| support audit | PASS | joint support report and claim boundary |

The output example matches the current verify schema. All paths referenced by README commands exist. The CLI synopsis contains all 10 implemented commands and matched parser help.

## Examples

| Example | Expected exit | Result | Notes |
| --- | ---: | --- | --- |
| integrity demo | 0 | PASS | inventory/freeze/verify |
| conditional support demo | 0 | PASS | schema accepted; support report created |
| Pareto audit demo | 0 | PASS | audit JSON created |
| leakage demo | 2 | PASS | intentional group overlap detected |
| gate demo | 0 | PASS | `INCONCLUSIVE` is a valid protocol outcome |

Every example is documented, uses only newly authored fixtures, runs without network access, writes to an isolated destination, and leaves the example source unchanged. Two complete runs produced byte-identical output trees for inventory, support, Pareto, leakage, and gate outputs; the two baseline runs also happened within the same UTC second and were byte-identical. All 14 commands across the two repetitions met their expected exit code in under one second total on the audit host.

No output contained a persisted personal absolute path or an overbroad scientific claim.
