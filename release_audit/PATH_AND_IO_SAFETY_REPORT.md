# Path and I/O Safety Report

## Result

`PASS` for the tested release risks.

| Risk | Behavior and evidence |
| --- | --- |
| Silent baseline overwrite | Refused by default; explicit `--force` required and recorded in each baseline row |
| Companion hash write | Temporary sibling file followed by atomic replace |
| Other structured output | CSV, JSON, and YAML writers use temporary files and atomic replace |
| Parent creation | Writers create the required parent directories |
| Inventory self-reference | Output path under root is lexically omitted with its subtree |
| Manifest self-reference | Baseline, companion, and temporary sibling are omitted when inside the root |
| Root escape | External symlink targets raise `UnsafePathError` |
| Internal/broken symlink | Link itself is hashed as link text, marked warning/excluded, and never followed |
| Special files | FIFO/device-like objects are rejected as unsupported rather than read |
| Relative paths | Inventory and baseline records use normalized root-relative POSIX paths |
| Unicode and spaces | Targeted tests pass |
| Case-fold collision | Distinct paths that collide case-insensitively are rejected |
| Read/permission failure | OS errors propagate to the CLI as concise structured errors; files are not silently skipped |
| Large file | SHA-256 uses 1 MiB streaming chunks |
| File changes during hash | Pre/post stat check raises an integrity failure |

Targeted tests cover root-escaping symlinks, broken internal symlinks, FIFO rejection, Unicode names, space-containing names, output self-pollution, nested baseline self-exclusion, overwrite refusal, and forced-overwrite evidence. Temporary virtual environments and documentation outputs were created outside the repository and removed after use.

Atomic replace provides protection against partial final files on the same filesystem. It is not a transaction across multiple unrelated files; the baseline and companion remain separate writes.
