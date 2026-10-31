# Stable file hashing hardening (local development, 2026-10-31)

Repository inventory and verification need hashes that reject observable file
replacement during an audit. The change is developed on an additive local
branch; public main and existing release tags remain available unchanged.

Two deterministic regressions failed on the inherited implementation: replacing
an opened file with an equal-size file whose mtime was preserved; and rewriting
the same inode while restoring mtime. Both returned a digest without reporting
that the object changed.

`sha256_file` now compares device, inode, mode, link count, size, nanosecond mtime,
ctime and available flags before opening, against the opened descriptor, and
after the read against both descriptor and pathname. Reads stop at the initial
size, so growth cannot create an unbounded loop. Observable mutation or short
reads raise `IntegrityFailure`; leaf symlinks and nonregular inputs are rejected.
The chunk size must be a positive integer, excluding booleans.

This does not promise an atomic filesystem snapshot, protection from privileged
metadata forgery, parent/root confinement, or historical identity. It does not
add hydration controls to legacy hashing; callers requiring confinement or
no-download guarantees must supply those separately. Permission
and access failures before the initial stat retain normal filesystem errors.

Tests exercise actual replacement/rewrite, deletion, truncation, growth, empty
files, multichunk reads, symlinks, directories, FIFOs and invalid chunk sizes.
This is an engineering fix, not a scientific result, release, consumer adoption,
or authorization to run research experiments.
