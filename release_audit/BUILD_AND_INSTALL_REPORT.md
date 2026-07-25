# Build and Install Report

## Build

Network access was not used. `python -m build` was unavailable, so the already-installed setuptools 82.0.1 backend was invoked directly, as permitted by the release protocol.

| Artifact | Result | Members | Size | SHA-256 |
| --- | --- | ---: | ---: | --- |
| `research_audit_kit-0.1.0-py3-none-any.whl` | PASS | 49 | 38,451 | `fdcac88d7afc52d407baec8990282528d599d005501afd0c080ef9586d47fd6c` |
| `research_audit_kit-0.1.0.tar.gz` | PASS | 75 | 27,135 | `df15330dfafde82d084611c9548a19dcfedc855675f7e0b08994e41ac9128bcc` |

Names and versions are consistent, and both archives passed the package-content scan. Checksums are recorded in `artifacts/checksums.sha256`.

Two fixed-epoch builds produced byte-identical wheels. The source-distribution member names and file payloads were identical, but 20 generated archive-entry timestamps differed, so the compressed source-distribution hash was not bit-reproducible. This is a documented P2 packaging limitation, not an installation or content-integrity failure.

## Isolated installations

Three independent temporary virtual environments were created with Python 3.13.13 and pip 26.0.1. All installations used `--no-index`, `--no-deps`, and no build isolation. PyYAML 6.0.3 was supplied from the already-installed local interpreter environment through read-only system site packages; no dependency download occurred.

| Path | Install | Import/version | CLI | End-to-end |
| --- | --- | --- | --- | --- |
| Editable | PASS | 0.1.0 from source checkout | help + inventory PASS | minimal smoke PASS |
| Wheel | PASS | 0.1.0 from temporary site-packages | all 10 command help paths PASS | five examples PASS |
| Source distribution | PASS | 0.1.0 from temporary site-packages | help PASS | inventory/freeze/verify PASS |

Wheel and source-distribution imports were performed outside the source checkout and resolved to temporary environment site-packages. Temporary environments were removed after the run. The local ignored `dist/` artifacts are retained for user review but were not uploaded.
