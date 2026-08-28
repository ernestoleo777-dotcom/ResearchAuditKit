#!/usr/bin/env bash
set -u

if [[ -z "${RAK_ACTION_ROOT:-}" ]]; then
  printf '%s\n' 'RAK_ACTION_ROOT is required.' >&2
  exit 2
fi

if [[ -z "${RAK_ACTION_RUNTIME_DIR:-}" || -z "${RAK_PYTHON_COMMAND:-}" ]]; then
  printf '%s\n' 'ResearchAuditKit Action runtime is not initialized.' >&2
  exit 2
fi

python_command="$RAK_PYTHON_COMMAND"
runner_temp="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
runtime_dir="$RAK_ACTION_RUNTIME_DIR"
case "$runtime_dir/" in
  "$runner_temp"/*) ;;
  *)
    printf '%s\n' 'ResearchAuditKit Action runtime is outside runner temporary storage.' >&2
    exit 2
    ;;
esac

result_file="${runtime_dir}/audit-result.json"
stdout_file="${result_file}.stdout"
summary_file="${runtime_dir}/job-summary.md"
workspace_root="${GITHUB_WORKSPACE:-$PWD}"

target_path="${RAK_INPUT_PATH:-.}"
if [[ "$target_path" != /* ]]; then
  target_path="$workspace_root/$target_path"
fi

policy_path="${RAK_INPUT_POLICY:-}"
if [[ -n "$policy_path" && "$policy_path" != /* ]]; then
  policy_path="$workspace_root/$policy_path"
fi

if ! "$python_command" -I -c 'import yaml; assert yaml.__version__ == "6.0.3"' 2>/dev/null; then
  printf '%s\n' 'ResearchAuditKit Action runtime dependency verification failed.' >&2
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
  "$python_command" -I "$RAK_ACTION_ROOT/action/runner.py" "${args[@]}"
) >"$stdout_file"
audit_code=$?
set -e

if [[ -f "$stdout_file" ]]; then
  cat "$stdout_file"
fi

if [[ -f "$result_file" ]]; then
  "$python_command" -I "$RAK_ACTION_ROOT/action/render-summary.py" "$result_file" >"$summary_file"
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    cat "$summary_file" >>"$GITHUB_STEP_SUMMARY"
  fi
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    audit_status=$(
      "$python_command" -I -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["status"])' "$result_file"
    )
    printf 'status=%s\n' "$audit_status" >>"$GITHUB_OUTPUT"
    printf 'result-file=%s\n' "$result_file" >>"$GITHUB_OUTPUT"
    printf 'exit-code=%s\n' "$audit_code" >>"$GITHUB_OUTPUT"
  fi
fi

exit "$audit_code"
