#!/usr/bin/env bash
set -u

if [[ -z "${RAK_ACTION_ROOT:-}" ]]; then
  printf '%s\n' 'RAK_ACTION_ROOT is required.' >&2
  exit 2
fi

python_command="${RAK_PYTHON_COMMAND:-python}"
runner_temp="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
result_file="${RAK_ACTION_RESULT_FILE:-${runner_temp}/researchauditkit-audit.json}"
stdout_file="${result_file}.stdout"
workspace_root="${GITHUB_WORKSPACE:-$PWD}"

target_path="${RAK_INPUT_PATH:-.}"
if [[ "$target_path" != /* ]]; then
  target_path="$workspace_root/$target_path"
fi

policy_path="${RAK_INPUT_POLICY:-}"
if [[ -n "$policy_path" && "$policy_path" != /* ]]; then
  policy_path="$workspace_root/$policy_path"
fi

if ! (
  cd "$RAK_ACTION_ROOT" || exit 2
  PYTHONPATH="$RAK_ACTION_ROOT/src" \
    "$python_command" -c 'import yaml; assert tuple(int(part) for part in yaml.__version__.split(".")[:1]) >= (6,)'
) 2>/dev/null; then
  printf '%s\n' 'ResearchAuditKit Action requires Python 3.10+ and PyYAML>=6 preinstalled.' >&2
  exit 2
fi

args=(
  audit
  "$target_path"
  --format "${RAK_INPUT_FORMAT:-human}"
  --output "$result_file"
  --fail-on "${RAK_INPUT_FAIL_ON:-release-blocker}"
)
if [[ -n "$policy_path" ]]; then
  args+=(--policy "$policy_path")
fi

set +e
(
  cd "$RAK_ACTION_ROOT" || exit 2
  PYTHONPATH="$RAK_ACTION_ROOT/src" \
    "$python_command" -m research_audit_kit.cli "${args[@]}"
) >"$stdout_file"
audit_code=$?
set -e

if [[ -f "$stdout_file" ]]; then
  cat "$stdout_file"
fi

if [[ -f "$result_file" ]]; then
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    (
      cd "$RAK_ACTION_ROOT" || exit 2
      PYTHONPATH="$RAK_ACTION_ROOT/src" \
        "$python_command" "$RAK_ACTION_ROOT/action/render-summary.py" "$result_file"
    ) >>"$GITHUB_STEP_SUMMARY"
  fi
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    audit_status=$(
      cd "$RAK_ACTION_ROOT" || exit 2
      PYTHONPATH="$RAK_ACTION_ROOT/src" \
        "$python_command" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["status"])' "$result_file"
    )
    printf 'status=%s\n' "$audit_status" >>"$GITHUB_OUTPUT"
    printf 'result-file=%s\n' "$result_file" >>"$GITHUB_OUTPUT"
  fi
fi

exit "$audit_code"
