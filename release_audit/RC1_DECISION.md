# RC1 Decision

## Decision

Engineering status: `RELEASE_CANDIDATE_READY`

Publication status: `BLOCKED_BY_LICENSE_SELECTION`

1. **Protected source unchanged:** Yes. The scientific baseline matched 33/33, its companion digest matched, the archive payload matched 18/18, all 510 nonvolatile closure-snapshot files matched, and no new volatile delta was observed.
2. **Git status:** Final branch is `main` with eight local commits and a clean tracked worktree. There is no remote or tag. Ignored local distributions remain under `dist/`.
3. **Package metadata:** Correct for an alpha RC: distribution `research-audit-kit`, import `research_audit_kit`, CLI `rak`, and single-source version 0.1.0. License remains truthfully unresolved.
4. **Builds:** Wheel and source distribution built successfully offline and passed archive-content scans; hashes are recorded.
5. **Clean installs:** Editable, wheel, and source-distribution paths passed in independent temporary environments. Wheel and source-distribution imports resolved outside the source checkout.
6. **CLI:** All 10 command help paths and functional flows were verified; 40 positive/negative command checks matched expected exits without tracebacks.
7. **README:** Install, four quickstart commands, all synopsis flows, and the verify output schema were executed and matched documentation.
8. **Examples:** 5/5 passed. The leakage example's exit 2 is intentional and correctly documented.
9. **API:** Suitable for an initial alpha release candidate, with narrow top-level exports, typed lower-level functions, explicit exceptions, centralized status vocabularies, and machine-readable returns. Permanent stability is not promised.
10. **Path/I/O:** Tested protections cover root-escaping symlinks, broken internal links, FIFO/special files, Unicode/spaces, case-fold collisions, output self-reference, atomic writes, streamed hashes, and explicit baseline overwrite.
11. **Privacy:** No personal identity, private path, email, credential, host, archived result, or sensitive filename inventory was found in release files or distributions.
12. **Network behavior:** No package runtime network call, telemetry, shell execution, or configuration-driven command execution was found.
13. **Tests:** 106 collected and passed, 0 failed, 0 skipped, 0 xfailed; `compileall` passed. Core status centralization and release-risk tests are included.
14. **CI:** Minimal Python 3.10–3.12 CI was added and locally validated. Status is `CI_CONFIGURATION_CREATED_NOT_REMOTE_EXECUTED`.
15. **License:** `READY_FOR_USER_LICENSE_SELECTION`; Apache-2.0 is the engineering recommendation, MIT is also reasonable, and no license file was created.
16. **P0/P1 blockers:** None remain. One P2 note records non-bit-reproducible generated timestamps in repeated source distributions; archive payloads were identical.
17. **Final engineering status:** `RELEASE_CANDIDATE_READY`.
18. **Final public status:** `BLOCKED_BY_LICENSE_SELECTION`.
19. **GitHub/PyPI permission:** Neither publication route is allowed. No remote, push, tag, release, or upload exists.
20. **Only next step:** `USER_SELECT_LICENSE_MIT_OR_APACHE_2_0`.

Release gates R1–R6 are PASS. R7 is `BLOCKED_BY_USER_DECISION`. This is an engineering tool RC, not a research project, paper artifact, or scientific-method claim.
