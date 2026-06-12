#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

APP_NAME="${APP_NAME:-bosgenesis-release-note-agent}"
IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-bosgenesis-release-note-agent}"
IMAGE_TAG="${IMAGE_TAG:-0.1.0}"
IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"
IMAGE_TAR="${IMAGE_REPOSITORY}-${IMAGE_TAG}.tar"
NAMESPACE="${NAMESPACE:-bosgenesis}"
REMOTE_USER="${REMOTE_USER:-taieuser}"
REMOTE_HOST="${REMOTE_HOST:-10.99.52.165}"
REMOTE_TMP_DIR="${REMOTE_TMP_DIR:-/tmp}"
REMOTE_IMAGE_TAR="${REMOTE_TMP_DIR}/${IMAGE_TAR}"
DEPLOY_METHOD="${DEPLOY_METHOD:-helm}"
HELM_RELEASE="${HELM_RELEASE:-bosgenesis-release-note-agent}"
HELM_CHART="${HELM_CHART:-helm/bosgenesis-release-note-agent}"
HELM_VALUES_FILE="${HELM_VALUES_FILE:-}"
KUSTOMIZE_DIR="${KUSTOMIZE_DIR:-deploy/k8s}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_IMAGE_TRANSFER="${SKIP_IMAGE_TRANSFER:-false}"
ENABLE_INGRESS="${ENABLE_INGRESS:-true}"
INGRESS_HOST="${INGRESS_HOST:-release-note-agent.bosgenesis.local}"
INGRESS_CLASS_NAME="${INGRESS_CLASS_NAME:-nginx}"
INGRESS_PATH="${INGRESS_PATH:-/}"
INGRESS_PATH_TYPE="${INGRESS_PATH_TYPE:-Prefix}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
API_DEPLOYMENT_NAME="${API_DEPLOYMENT_NAME:-${HELM_RELEASE}-api}"
MCP_DEPLOYMENT_NAME="${MCP_DEPLOYMENT_NAME:-${HELM_RELEASE}-mcp}"
API_SERVICE_NAME="${API_SERVICE_NAME:-${HELM_RELEASE}-api}"
MCP_SERVICE_NAME="${MCP_SERVICE_NAME:-${HELM_RELEASE}-mcp}"

log() {
  printf '\n[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 127
  fi
}

adopt_helm_resource() {
  local kind="$1"
  local name="$2"

  if kubectl get "${kind}" "${name}" -n "${NAMESPACE}" >/dev/null 2>&1; then
    log "Adopting existing ${kind}/${name} into Helm release ${HELM_RELEASE}"
    kubectl label "${kind}" "${name}" \
      app.kubernetes.io/managed-by=Helm \
      -n "${NAMESPACE}" \
      --overwrite
    kubectl annotate "${kind}" "${name}" \
      meta.helm.sh/release-name="${HELM_RELEASE}" \
      meta.helm.sh/release-namespace="${NAMESPACE}" \
      -n "${NAMESPACE}" \
      --overwrite
  fi
}

adopt_existing_helm_resources() {
  if helm status "${HELM_RELEASE}" -n "${NAMESPACE}" >/dev/null 2>&1; then
    return
  fi

  log "Checking for existing non-Helm resources to adopt"
  adopt_helm_resource configmap "${HELM_RELEASE}-config"
  adopt_helm_resource persistentvolumeclaim "${HELM_RELEASE}-data"
  adopt_helm_resource service "${API_SERVICE_NAME}"
  adopt_helm_resource service "${MCP_SERVICE_NAME}"
  adopt_helm_resource deployment "${API_DEPLOYMENT_NAME}"
  adopt_helm_resource deployment "${MCP_DEPLOYMENT_NAME}"
  adopt_helm_resource ingress "${HELM_RELEASE}"
}

validate_helm_chart_files() {
  local helmignore_file="${HELM_CHART}/.helmignore"

  if [ -f "${helmignore_file}" ] && grep -F "**" "${helmignore_file}" >/dev/null 2>&1; then
    echo "Unsupported Helm ignore pattern found in ${helmignore_file}: double-star (**) is not supported by this Helm version." >&2
    echo "Use explicit single-level patterns such as templates/SPEC.md instead." >&2
    exit 1
  fi
}

require_cmd kubectl
require_cmd ssh
require_cmd scp

if [ "${DEPLOY_METHOD}" = "helm" ]; then
  require_cmd helm
  validate_helm_chart_files
fi

if [ "${SKIP_BUILD}" != "true" ]; then
  require_cmd docker
  log "Building image ${IMAGE}"
  docker build -t "${IMAGE}" .

  log "Saving image to ${IMAGE_TAR}"
  docker save "${IMAGE}" -o "${IMAGE_TAR}"
fi

if [ "${SKIP_IMAGE_TRANSFER}" != "true" ]; then
  log "Copying image tar to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_IMAGE_TAR}"
  scp "${IMAGE_TAR}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_IMAGE_TAR}"

  log "Importing image into containerd on ${REMOTE_HOST}"
  ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo ctr -n k8s.io images import '${REMOTE_IMAGE_TAR}'"

  log "Verifying imported image on ${REMOTE_HOST}"
  ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo ctr -n k8s.io images list | grep '${IMAGE_REPOSITORY}'"
fi

log "Ensuring namespace ${NAMESPACE} exists"
kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

if [ "${DEPLOY_METHOD}" = "helm" ]; then
  ROLLOUT_TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

  log "Deploying with Helm release ${HELM_RELEASE}"
  adopt_existing_helm_resources

  helm_args=(
    upgrade
    --install
    "${HELM_RELEASE}"
    "${HELM_CHART}"
    --namespace "${NAMESPACE}"
    --set fullnameOverride="${HELM_RELEASE}"
    --set image.repository="${IMAGE_REPOSITORY}"
    --set image.tag="${IMAGE_TAG}"
    --set ingress.enabled="${ENABLE_INGRESS}"
    --set ingress.hosts[0].host="${INGRESS_HOST}"
    --set ingress.hosts[0].paths[0].path="${INGRESS_PATH}"
    --set ingress.hosts[0].paths[0].pathType="${INGRESS_PATH_TYPE}"
    --set ingress.hosts[0].paths[0].service="api"
    --set ingress.hosts[0].paths[1].path="/mcp"
    --set ingress.hosts[0].paths[1].pathType="Prefix"
    --set ingress.hosts[0].paths[1].service="mcp"
    --set config.logLevel="${LOG_LEVEL}"
    --set rolloutTimestamp="${ROLLOUT_TIMESTAMP}"
  )
  if [ -n "${INGRESS_CLASS_NAME}" ]; then
    helm_args+=(--set ingress.className="${INGRESS_CLASS_NAME}")
  fi
  if [ -n "${HELM_VALUES_FILE}" ]; then
    helm_args+=(-f "${HELM_VALUES_FILE}")
  fi
  helm "${helm_args[@]}"
else
  log "Applying Kubernetes manifests from ${KUSTOMIZE_DIR}"
  kubectl apply -k "${KUSTOMIZE_DIR}"
fi

log "Waiting for API rollout"
kubectl rollout status "deployment/${API_DEPLOYMENT_NAME}" -n "${NAMESPACE}"

log "Waiting for MCP rollout"
kubectl rollout status "deployment/${MCP_DEPLOYMENT_NAME}" -n "${NAMESPACE}"

log "Pods"
kubectl get pod -n "${NAMESPACE}" -o wide | grep "${HELM_RELEASE}" || true

log "Services"
kubectl get svc "${API_SERVICE_NAME}" "${MCP_SERVICE_NAME}" -n "${NAMESPACE}"

if [ "${ENABLE_INGRESS}" = "true" ]; then
  log "Ingress"
  kubectl get ingress "${HELM_RELEASE}" -n "${NAMESPACE}" || true
fi

log "Health check hints"
echo "kubectl port-forward -n ${NAMESPACE} svc/${API_SERVICE_NAME} 8080:8080"
echo "curl http://localhost:8080/health"
echo "kubectl port-forward -n ${NAMESPACE} svc/${MCP_SERVICE_NAME} 8090:8090"
echo "curl http://localhost:8090/mcp/tools"
if [ "${ENABLE_INGRESS}" = "true" ]; then
  echo "Ingress host: ${INGRESS_HOST}"
  echo "curl http://${INGRESS_HOST}/health"
  echo "curl http://${INGRESS_HOST}/mcp/tools"
fi

log "Done"
