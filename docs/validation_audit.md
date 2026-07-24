# Validation Audit

Split manifests bind row IDs, coordinate IDs, roles, folds, groups, seeds, and dataset hashes. Leakage checks cover repeated IDs, coordinate overlap, group overlap, temporal ordering, branch overlap, and calibration/test overlap. Fold-local checks require component metadata; absent or incomplete logs yield `UNVERIFIED_FROM_METADATA` rather than a clean bill of health.

