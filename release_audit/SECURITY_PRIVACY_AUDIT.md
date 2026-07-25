# Security and Privacy Audit

## Scope and result

`PASS` for the defined release-engineering checks. This is a focused internal review, not a penetration test or third-party security certification.

## Input handling

- YAML uses `yaml.safe_load`; no Python object construction or command execution is enabled.
- YAML, JSON, and CSV document roots are type-checked where consumed.
- CSV rejects empty input, absent/empty headers, duplicate columns, and inconsistent row widths.
- CSV exports neutralize values beginning with `=`, `+`, or `@`, and nonnumeric `-` prefixes; ordinary negative numeric values remain unchanged.
- Malformed text encodings and parser errors become controlled CLI errors without tracebacks.
- Hashing reads in 1 MiB chunks and compares file stat metadata before and after reading. A concurrent file change raises `IntegrityFailure`. A residual TOCTOU window remains inherent between independent filesystem operations and is documented rather than overstated.

## Execution and data flow

- No `shell=True`, subprocess command construction, configuration-driven code execution, telemetry, credential storage, or runtime network call was found in package source.
- The package does not read outside a user-supplied path. Inventory traversal rejects symlinks escaping the declared root.
- The runtime dependency set is limited to PyYAML.

## Privacy rescan

Tracked release files were scanned for personal names, home and temporary absolute paths, email addresses, credential/token/key markers, hostnames, shell history, archived project paths, and symlinks. No match requiring removal was found. Package payloads were separately scanned and passed.

The audit reports retain aggregate protected-source counts and checks, not protected filenames or hash inventories. The only claim-scan hit is the word `benchmark` in an explicitly negated README scope boundary; it is classified `NEGATED_SCOPE_BOUNDARY`.
