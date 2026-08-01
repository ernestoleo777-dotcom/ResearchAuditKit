# Metadata Update Report

The setuptools PEP 621 metadata now uses the SPDX license expression `Apache-2.0`. Distribution name (`research-audit-kit`), dynamic version (`0.1.0`), import package, `rak` entry point, Python requirement, and runtime dependency set are unchanged. `MANIFEST.in` explicitly includes `LICENSE` and continues to prune internal audit directories.

Wheel METADATA and sdist PKG-INFO both declare `License-Expression: Apache-2.0` and include LICENSE. The detailed consistency evidence is in `checks/metadata_consistency.csv`.
