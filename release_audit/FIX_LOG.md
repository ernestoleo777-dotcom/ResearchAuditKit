# Release Hardening Fix Log

| issue_id | severity | file | problem | fix | test | status | commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PKG-001 | P1 | `pyproject.toml` | Version was duplicated in metadata and code | Made package constant the dynamic metadata source; used generic author label | version metadata/CLI consistency | RESOLVED | f2f1cb3 |
| PKG-002 | P1 | `MANIFEST.in` | Source distribution included tests and audit material under default discovery | Added explicit minimal source-distribution policy | wheel/sdist member scan | RESOLVED | f2f1cb3 |
| DOC-001 | P1 | `README.md` | Install context, overwrite behavior, and output example were incomplete/inaccurate | Corrected instructions and schema example | README command and schema tests | RESOLVED | f2f1cb3 |
| DOC-002 | P1 | `examples/` | Four examples lacked local execution notes and claim boundaries | Added concise example READMEs | 5/5 isolated example runs | RESOLVED | f2f1cb3 |
| CLI-001 | P0 | `cli.py` | Parser/data/OS failures could expose raw exceptions or inconsistent exits | Added controlled error boundary and consistent exit 2 | malformed YAML/JSON/CSV/path tests | RESOLVED | 1ffad54 |
| IO-001 | P0 | baseline and deviation writers | Forced replacement was not preserved as baseline evidence; ledger rewrite was not atomic | Added `forced_overwrite` field and atomic replacement | refusal/force/ledger tests | RESOLVED | 1ffad54 |
| IO-002 | P0 | inventory/baseline | Output self-reference and symlink escape policies were incomplete | Added lexical omissions, root escape rejection, and non-follow symlink policy | self-pollution, escape, broken link tests | RESOLVED | 1ffad54 |
| SEC-001 | P1 | CSV and hashing | Empty/duplicate/irregular CSV and formula injection were not fully controlled; concurrent hash mutation was unchecked | Added validation/neutralization and pre/post stat check | CSV security and hashing tests | RESOLVED | 1ffad54 |
| API-001 | P2 | exceptions/constants/core modules | Exception categories and shared serialized status references were incomplete | Added explicit hierarchy and centralized core status constants | full suite + literal scan | RESOLVED | Commit 8 |
| IO-003 | P1 | inventory | Special file and broken-link behavior lacked release-risk regression coverage | Added FIFO rejection and broken internal symlink tests | targeted inventory tests | RESOLVED | Commit 8 |
| CI-001 | P1 | `.github/workflows/ci.yml` | No publication-ready minimal CI existed | Added restricted 3.10–3.12 test/compile/help workflow | local YAML and command validation | RESOLVED | Commit 8 |
| PKG-003 | P2 | local setuptools sdist | Repeated fixed-epoch source distributions retain generated member timestamps | Recorded payload equality and non-bit-reproducible archive hash; no functional change | repeated archive member/hash comparison | DOCUMENTED_NON_BLOCKING | Commit 8 |

No P0 or P1 issue remains open. PKG-003 is a packaging reproducibility limitation, not a content, installation, or publication-safety blocker.
