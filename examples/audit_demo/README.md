# Unified audit demo

These synthetic repositories exercise the public `rak audit` contract:

- `pass_repo` passes the zero-configuration baseline;
- `warning_repo` omits a repository-root license and returns `WARNING`;
- `blocker_repo` declares a required artifact in `.rak/policy.yaml` and omits it.

The fixtures contain no research data and establish no scientific or reproducibility claim.
