# Pre-fix acceptance note

The first Phase 1 acceptance review identified one P1 usability issue: when a
requested prediction seal output already existed, the refusal did not tell the
user how to make an explicit replacement safely.

Commit `346c0425ecae161dc57e9d7d057b2cdf18f52986` changes only the refusal
message and its CLI regression coverage. It retains default refusal, requires
an explicit `--force` opt-in, and does not change seal content, digesting,
schema, or verification behavior.

The earlier acceptance result is retained as historical context and is not the
authoritative decision. The post-fix results in this directory are the
authoritative acceptance basis.
