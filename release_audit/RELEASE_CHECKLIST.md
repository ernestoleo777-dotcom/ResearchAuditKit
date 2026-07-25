# RC1 Release Checklist

## Source and scope

- [x] Protected source scientific baseline matched 33/33
- [x] Protected final archive payload matched 18/18
- [x] Phase 0 audit evidence remained byte-identical
- [x] No archived data, result, path, or symlink entered the package
- [x] Changes remained within release-engineering scope

## Package and installation

- [x] Distribution/import/CLI/version metadata agree
- [x] Wheel built and content-scanned
- [x] Source distribution built and content-scanned
- [x] SHA-256 values recorded
- [x] Editable install passed offline
- [x] Wheel install passed outside source checkout
- [x] Source-distribution install passed outside source checkout
- [x] Local ignored artifacts were not uploaded

## Behavior and documentation

- [x] 106 tests passed with no skip/xfail
- [x] `compileall` passed
- [x] All 10 CLI help paths passed
- [x] Invalid input and scientific-failure exit behavior passed
- [x] README install, quickstart, synopsis flows, and output schema were executed
- [x] Five examples passed, including the expected negative leakage example
- [x] Forbidden claim scan passed

## Safety and publication

- [x] YAML safe-loading checked
- [x] Path escape and overwrite protections checked
- [x] Privacy and forbidden-asset rescans passed
- [x] Minimal CI configuration locally validated
- [ ] User selected MIT or Apache-2.0
- [ ] Formal `LICENSE` file reviewed and added
- [ ] Remote publication explicitly authorized

Engineering RC is ready. Public release is not permitted until the three unchecked user-controlled items are resolved, beginning with license selection.
