#!/bin/bash
set -euo pipefail

#
# Deploy mortgage-ai to OpenShift
#
# Prerequisites:
#   - oc login (logged into the target cluster)
#   - podman login quay.io (authenticated to push images)
#   - helm installed
#   - .env file with LLM_* variables (or set them as environment variables)
#
# Usage:
#   ./deploy.sh                          # deploy with defaults
#   REGISTRY=quay.io/myorg ./deploy.sh   # override image registry/org
#   NAMESPACE=my-ns ./deploy.sh          # override namespace
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- Configuration (override via environment) --------------------------------
REGISTRY="${REGISTRY:-quay.io/sauagarw}"
NAMESPACE="${NAMESPACE:-mortgage-ai}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
HELM_CHART="./deploy/helm/mortgage-ai"
HELM_TIMEOUT="${HELM_TIMEOUT:-15m}"
ENV_FILE="${ENV_FILE:-.env}"
PLATFORM="${PLATFORM:-linux/amd64}"

# Detect cluster apps domain
CLUSTER_DOMAIN="$(oc whoami --show-server 2>/dev/null \
  | sed -E 's|https://api\.([^:]+).*|apps.\1|' || echo "")"
ROUTE_HOST="${ROUTE_HOST:-${NAMESPACE}-${NAMESPACE}.${CLUSTER_DOMAIN}}"

# --- Load .env ----------------------------------------------------------------
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment from $ENV_FILE"
  set -a; source "$ENV_FILE"; set +a
fi

# Resolve VITE_API_BASE_URL for baking into the UI build
VITE_API_BASE_URL="${VITE_API_BASE_URL:-https://${ROUTE_HOST}}"

# --- Build images -------------------------------------------------------------
echo ""
echo "=== Building container images ==="

echo "Building API image..."
podman build --platform "${PLATFORM}" -f packages/api/Containerfile \
  -t "${REGISTRY}/mortgage-ai-api:${IMAGE_TAG}" .

echo "Building UI image (VITE_API_BASE_URL=${VITE_API_BASE_URL})..."
podman build --platform "${PLATFORM}" -f packages/ui/Containerfile \
  --build-arg "VITE_API_BASE_URL=${VITE_API_BASE_URL}" \
  -t "${REGISTRY}/mortgage-ai-ui:${IMAGE_TAG}" .

echo "Building Worker image..."
podman build --platform "${PLATFORM}" -f packages/api/Containerfile.worker \
  -t "${REGISTRY}/mortgage-ai-worker:${IMAGE_TAG}" .

echo "Building DB migration image..."
podman build --platform "${PLATFORM}" -f packages/db/Containerfile \
  -t "${REGISTRY}/mortgage-ai-db:${IMAGE_TAG}" .

# --- Push images --------------------------------------------------------------
echo ""
echo "=== Pushing images to ${REGISTRY} ==="

podman push "${REGISTRY}/mortgage-ai-api:${IMAGE_TAG}"
podman push "${REGISTRY}/mortgage-ai-ui:${IMAGE_TAG}"
podman push "${REGISTRY}/mortgage-ai-worker:${IMAGE_TAG}"
podman push "${REGISTRY}/mortgage-ai-db:${IMAGE_TAG}"

# --- Create namespace ---------------------------------------------------------
echo ""
echo "=== Ensuring namespace ${NAMESPACE} exists ==="
oc new-project "${NAMESPACE}" 2>/dev/null || echo "Project ${NAMESPACE} already exists"

# --- Deploy via Helm ----------------------------------------------------------
echo ""
echo "=== Deploying via Helm ==="

helm upgrade --install mortgage-ai "$HELM_CHART" \
  --namespace "${NAMESPACE}" \
  --timeout "${HELM_TIMEOUT}" \
  --wait --wait-for-jobs \
  --set global.imageRegistry="${REGISTRY%%/*}" \
  --set global.imageRepository="${REGISTRY#*/}" \
  --set global.imageTag="${IMAGE_TAG}" \
  --set routes.sharedHost="${ROUTE_HOST}" \
  --set secrets.POSTGRES_DB="${POSTGRES_DB:-mortgage-ai}" \
  --set secrets.POSTGRES_USER="${POSTGRES_USER:-user}" \
  --set secrets.POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changeme}" \
  --set secrets.DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-user}:${POSTGRES_PASSWORD:-changeme}@mortgage-ai-db:5432/${POSTGRES_DB:-mortgage-ai}" \
  --set secrets.DEBUG="${DEBUG:-false}" \
  --set secrets.ALLOWED_HOSTS="${ALLOWED_HOSTS:-[\"*\"]}" \
  --set secrets.REDIS_URL="${REDIS_URL:-redis://mortgage-ai-redis:6379/0}" \
  --set secrets.MINIO_ENDPOINT="${MINIO_ENDPOINT:-mortgage-ai-minio:9000}" \
  --set secrets.MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}" \
  --set secrets.MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-changeme}" \
  --set secrets.MINIO_BUCKET="${MINIO_BUCKET:-mortgage-documents}" \
  --set secrets.LLM_PROVIDER="${LLM_PROVIDER:-openai}" \
  --set secrets.LLM_BASE_URL="${LLM_BASE_URL:-https://api.openai.com/v1}" \
  --set secrets.LLM_API_KEY="${LLM_API_KEY:-}" \
  --set secrets.LLM_MODEL="${LLM_MODEL:-gpt-4o}" \
  --set secrets.VITE_API_BASE_URL="${VITE_API_BASE_URL}" \
  --set secrets.VITE_ENVIRONMENT="production"

# --- Status -------------------------------------------------------------------
echo ""
echo "=== Deployment status ==="
oc get pods -n "${NAMESPACE}"
echo ""
oc get routes -n "${NAMESPACE}"
echo ""
echo "Application URL: https://${ROUTE_HOST}"
