# Integrity Model

An integrity policy classifies files as scientific assets, volatile metadata, generated artifacts, caches, temporary files, or unclassified files. Baselines store relative paths and SHA-256 digests. Included mismatches and missing required files fail the gate; volatile changes warn. Matching bytes do not establish the scientific correctness of their content.

Required-file declarations must already be canonical portable relative file
paths. Policy loading rejects absolute, traversal, Windows-drive, UNC/device,
backslash, control-character, empty, and redundant path forms. Inventory also
checks existing symlink components without probing an escaping target. The same
validator governs audit, inventory, freeze, and policy records reloaded by
verification; unsafe values cannot become baseline paths or public findings.

Manifest writers exclude the manifest, companion digest, and temporary write file to avoid self-reference.
