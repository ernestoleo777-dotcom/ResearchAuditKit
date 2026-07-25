# API Stability Report

## Result

`PASS_WITH_NOTES` for an initial alpha release candidate.

- Top-level `research_audit_kit` exports only `__version__`; implementation modules are not indiscriminately re-exported.
- The CLI and lower-level functions return dictionaries/lists suitable for JSON or CSV serialization.
- Version metadata has one source and is covered by a consistency test.
- Shared gate status strings are defined in `constants.py` and referenced by core modules. Domain-specific status vocabularies are also centralized there.
- The exception hierarchy distinguishes configuration, input validation, integrity failure, overwrite protection, unsafe path, unsupported format, and internal invariant cases under `AuditError`.
- The CLI catches expected user/input/OS/parser failures and does not use a blanket `except Exception`.
- Public callables carry type annotations; modules and principal public functions have docstrings.
- Paths are accepted as strings or `Path` objects. Portable outputs record paths relative to the declared root. User-supplied error paths may appear in immediate terminal errors but are not embedded in packaged fixtures.

There is no promise of permanent API stability at version 0.1.0. Submodule imports are usable but should be treated as alpha surface. No large API refactor was performed.
