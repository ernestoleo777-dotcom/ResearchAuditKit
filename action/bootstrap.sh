#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${RAK_ACTION_ROOT:-}" || -z "${RUNNER_TEMP:-}" || -z "${GITHUB_OUTPUT:-}" ]]; then
  printf '%s\n' 'ResearchAuditKit Action bootstrap environment is incomplete.' >&2
  exit 2
fi

runtime_dir=$(mktemp -d "${RUNNER_TEMP%/}/researchauditkit-action.XXXXXX")
mkdir -p "$runtime_dir/tmp"
python -I -m venv "$runtime_dir/venv"

if [[ -x "$runtime_dir/venv/bin/python" ]]; then
  python_command="$runtime_dir/venv/bin/python"
elif [[ -x "$runtime_dir/venv/Scripts/python.exe" ]]; then
  python_command="$runtime_dir/venv/Scripts/python.exe"
else
  printf '%s\n' 'ResearchAuditKit Action could not locate its isolated interpreter.' >&2
  exit 2
fi

TMPDIR="$runtime_dir/tmp" "$python_command" -I -m pip \
  --isolated \
  --disable-pip-version-check \
  --no-input \
  --no-cache-dir \
  install \
  --index-url https://pypi.org/simple \
  --require-hashes \
  --only-binary=:all: \
  --no-deps \
  --requirement "$RAK_ACTION_ROOT/action/requirements.lock"

printf 'runtime-dir=%s\n' "$runtime_dir" >>"$GITHUB_OUTPUT"
printf 'python-command=%s\n' "$python_command" >>"$GITHUB_OUTPUT"
