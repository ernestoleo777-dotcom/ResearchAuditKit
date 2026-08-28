# Extension boundaries

The canonical P1 interchange point is the versioned `researchauditkit.audit/v1` JSON result. Future adapters may consume that result or translate separately supplied standard records, but must not redefine external standards or upgrade mechanical findings into scientific claims.

| Possible adapter | Permitted boundary | Explicitly deferred |
| --- | --- | --- |
| SARIF | Map findings only after preserving blocker/warning/unresolved semantics and locations | No lossy severity-only mapping in P1 |
| RO-Crate | Reference an audit result as an external/generated file under an applicable profile | No RO-Crate vocabulary or validator implementation |
| SLSA / in-toto | Attach a released audit result as one subject/material or external attestation payload | No provenance generator or trust claim |
| CodeMeta | Describe the ResearchAuditKit software release | No paper/claim metadata inference |
| IDE/editor | Display canonical findings and locations | No VS Code extension or background scanner |
| MCP/web service | Invoke an explicitly installed local CLI with user authorization | No service, telemetry, upload, database, or MCP server in P1 |

Adapters must pin the input schema version, preserve source authority, expose unsupported mappings, and retain the non-certification boundary.
