#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-bosgenesis-release-note-agent}"
IMAGE_NAME="${IMAGE_NAME:-${APP_NAME}}"
IMAGE_TAG="${IMAGE_TAG:-local-smoke}"
CONTAINER_NAME="${CONTAINER_NAME:-${APP_NAME}-smoke}"
HOST_PORT="${HOST_PORT:-18080}"
DATA_DIR="${DATA_DIR:-$(pwd)/data/container-smoke}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${HOST_PORT}}"

log() {
  printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

mkdir -p \
  "${DATA_DIR}/workspaces" \
  "${DATA_DIR}/artifacts" \
  "${DATA_DIR}/jobs" \
  "${DATA_DIR}/logs"

log "Building image ${IMAGE_NAME}:${IMAGE_TAG}"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

cleanup

log "Starting container ${CONTAINER_NAME} on ${BASE_URL}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${HOST_PORT}:8080" \
  -v "${DATA_DIR}:/data" \
  -e GRNA_WORKSPACE_ROOT=/data/workspaces \
  -e GRNA_ARTIFACT_ROOT=/data/artifacts \
  -e GRNA_JOB_ROOT=/data/jobs \
  -e GRNA_LOG_ROOT=/data/logs \
  "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null

log "Waiting for health endpoint"
for _ in $(seq 1 30); do
  if curl -fsS "${BASE_URL}/health" >/dev/null; then
    break
  fi
  sleep 2
done

log "Checking health"
curl -fsS "${BASE_URL}/health"
printf '\n'

log "Checking readiness"
curl -fsS "${BASE_URL}/ready"
printf '\n'

log "Checking configurable data roots"
docker exec "${CONTAINER_NAME}" test -d /data/workspaces
docker exec "${CONTAINER_NAME}" test -d /data/artifacts
docker exec "${CONTAINER_NAME}" test -d /data/jobs
docker exec "${CONTAINER_NAME}" test -d /data/logs

log "Container smoke test passed"
