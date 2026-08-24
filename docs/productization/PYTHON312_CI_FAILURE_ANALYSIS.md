# Python 3.12 CI Failure Analysis

## Incident

The Python 3.12 job in CI run `32747208953` failed in
`test_wheel_and_sdist_public_content_contract`. The test launched the active
interpreter and imported `setuptools.build_meta` directly, but that interpreter
did not have `setuptools` installed. Python 3.10 and 3.11 passed because their
job environments happened to make the backend importable; the development
dependency declaration did not guarantee that state.

## Root cause

`pyproject.toml` correctly declared `setuptools>=68` under `[build-system]`.
That declaration is consumed by a PEP 517 frontend when it creates an isolated
build environment; it does not install `setuptools` into the interpreter that
runs the test suite. The existing `dev` extra declared `pytest` and development
tools but omitted the build frontend and backend used by the package-content
test. Direct backend invocation therefore relied on incidental runner contents.

The failure is an undeclared test/build dependency combined with an incorrect
direct-backend test entry point. It is not a runtime dependency or product
behavior failure.

## Dependency boundary

- Core runtime: `PyYAML`; no packaging tool is required by installed commands.
- Build system: `setuptools>=68`, as declared by `[build-system]`.
- Development acceptance: `build`, `setuptools`, and `wheel`, declared in the
  existing `dev` extra alongside `pytest`.

## Fix

The package-content contract now invokes the standard `python -m build` PEP 517
frontend. It uses `--no-isolation` intentionally: CI and local acceptance first
install `.[dev]`, so all frontend and backend requirements are explicit and the
test does not download dependencies into an implicit temporary build
environment. The existing CI installation entry point, `python -m pip install
-e ".[dev]"`, is shared with local acceptance and requires no matrix change.

This change does not add a core dependency, modify runtime code, change the CLI,
or alter the public API.
