# Integrity Model

An integrity policy classifies files as scientific assets, volatile metadata, generated artifacts, caches, temporary files, or unclassified files. Baselines store relative paths and SHA-256 digests. Included mismatches and missing required files fail the gate; volatile changes warn. Matching bytes do not establish the scientific correctness of their content.

Manifest writers exclude the manifest, companion digest, and temporary write file to avoid self-reference.

