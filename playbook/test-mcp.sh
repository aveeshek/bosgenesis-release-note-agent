#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-bosgenesis}"
INGRESS_HOST="${INGRESS_HOST:-release-note-agent.bosgenesis.local}"
API_SERVICE_NAME="${API_SERVICE_NAME:-bosgenesis-release-note-agent-api}"
MCP_SERVICE_NAME="${MCP_SERVICE_NAME:-bosgenesis-release-note-agent-mcp}"
TEST_REPO_URL="${TEST_REPO_URL:-https://github.com/aveeshek/bosgenesis-mop-creation-agent}"
USE_INGRESS="${USE_INGRESS:-true}"

log() {
  printf '\n[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 127
  fi
}

request() {
  local method="$1"
  local url="$2"
  local body="${3:-}"

  if [ -n "${body}" ]; then
    curl -fsS \
      -X "${method}" \
      -H "Content-Type: application/json" \
      --data "${body}" \
      "${url}"
  else
    curl -fsS -X "${method}" "${url}"
  fi
}

extract_job_id() {
  python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["job_id"])'
}

require_cmd curl
require_cmd python3

if [ "${USE_INGRESS}" = "true" ]; then
  BASE_URL="http://${INGRESS_HOST}"
  log "Testing MCP through ingress ${BASE_URL}"
else
  require_cmd kubectl
  log "Testing MCP through port-forward to service/${MCP_SERVICE_NAME}"
  kubectl port-forward -n "${NAMESPACE}" "svc/${MCP_SERVICE_NAME}" 8090:8090 >/tmp/grna-mcp-port-forward.log 2>&1 &
  PF_PID="$!"
  trap 'kill "${PF_PID}" >/dev/null 2>&1 || true' EXIT
  sleep 2
  BASE_URL="http://127.0.0.1:8090"
fi

log "Health"
request GET "${BASE_URL}/health"
echo

log "Readiness"
request GET "${BASE_URL}/ready"
echo

log "List MCP tools"
request GET "${BASE_URL}/mcp/tools"
echo

log "Start scan job"
SCAN_RESPONSE="$(request POST "${BASE_URL}/mcp/tools/github_release_scan_start" "{\"repo_url\":\"${TEST_REPO_URL}\",\"analysis_depth\":\"fast\",\"output_formats\":[\"markdown\",\"html\"]}")"
echo "${SCAN_RESPONSE}"
JOB_ID="$(printf '%s' "${SCAN_RESPONSE}" | extract_job_id)"

log "Get scan status for ${JOB_ID}"
request POST "${BASE_URL}/mcp/tools/github_release_scan_status" "{\"job_id\":\"${JOB_ID}\"}"
echo

log "Get artifact metadata for ${JOB_ID}"
request POST "${BASE_URL}/mcp/tools/github_release_get_artifact" "{\"job_id\":\"${JOB_ID}\"}"
echo

log "MCP smoke test completed"
