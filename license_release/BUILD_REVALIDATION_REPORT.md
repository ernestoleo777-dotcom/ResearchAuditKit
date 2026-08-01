# Build and Clean-Install Revalidation

Old ignored distribution artifacts were recorded and removed before rebuilding. Local setuptools `build_meta` rebuilt the wheel and sdist without dependency resolution or network access. The wheel has 50 members and the sdist has 64 members; both contain LICENSE and Apache-2.0 Core Metadata. Neither contains `license_release/`, `audit/`, `release_audit/`, VCS data, PDFs, spreadsheets, pickle files, `.DS_Store`, or cache content.

Three independent temporary virtual environments, created with system site packages only, passed all 51 checks: editable install, wheel install, and sdist install each passed installation, import/version, all CLI help commands, and minimal integrity/support workflows. The environments were removed after validation.

Artifact SHA-256 values are in `artifacts/checksums.sha256`; member-level evidence is in `checks/package_content_scan.csv`.
