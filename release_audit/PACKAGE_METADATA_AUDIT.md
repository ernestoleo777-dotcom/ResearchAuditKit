# Package Metadata Audit

## Result

`PASS` for RC engineering. The license remains intentionally unresolved and blocks public release.

| Item | Observed | Assessment |
| --- | --- | --- |
| Distribution name | `research-audit-kit` | Normalized equivalent of ResearchAuditKit; PASS |
| Import name | `research_audit_kit` | PASS |
| CLI entry point | `rak = research_audit_kit.cli:main` | PASS |
| Version | 0.1.0 from `research_audit_kit.constants.__version__` | Single source; package and CLI agree |
| Python requirement | `>=3.10` | Syntax parsed against Python 3.10; local execution used Python 3.13.13; CI covers 3.10–3.12 when remotely run |
| Runtime dependencies | `PyYAML>=6.0` | Minimal and used for safe YAML parsing |
| Development extra | pytest, pre-commit, ruff | Correctly optional |
| Build backend | `setuptools.build_meta`, setuptools >=68 | PASS |
| Layout/discovery | `src/` layout; setuptools discovery in `src` | PASS |
| README/description | Present and claim-bounded | PASS |
| Author | Generic project contributor label | No personal data |
| Project URLs/DOI | Absent | No fabricated links or DOI |
| License | No formal license selected | Correctly unresolved; `LICENSE_STATUS.md` is status evidence only |

## Inclusion policy

The wheel contains only package code and distribution metadata. The source distribution additionally contains the minimum project metadata and reusable configuration templates. Tests, examples, docs, Phase 0 audit material, release-audit material, caches, temporary baselines, and local build output are excluded by `MANIFEST.in` and verified by archive inspection.

Final archive sizes are 38,451 bytes for the wheel and 27,135 bytes for the source distribution. No private absolute path, archived source identifier, cache, `.DS_Store`, pickle, PDF, workbook, or local environment was found.

Version 0.1.0 was preserved because it already existed and was internally reasonable. It is classified as alpha and does not imply a stable public API or publication.
