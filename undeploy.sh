#!/bin/bash
set -euo pipefail

#
# Undeploy mortgage-ai from OpenShift
#
# Usage:
#   ./undeploy.sh                      # undeploy from default namespace
#   NAMESPACE=my-ns ./undeploy.sh      # undeploy from specific namespace
#   DELETE_PROJECT=true ./undeploy.sh   # also delete the OpenShift project
#

NAMESPACE="${NAMESPACE:-mortgage-ai}"
DELETE_PROJECT="${DELETE_PROJECT:-false}"
RELEASE_NAME="mortgage-ai"

echo "=== Undeploying ${RELEASE_NAME} from namespace ${NAMESPACE} ==="

# Uninstall Helm release
echo "Removing Helm release..."
helm uninstall "${RELEASE_NAME}" --namespace "${NAMESPACE}" 2>/dev/null \
  || echo "Release ${RELEASE_NAME} not found (may already be removed)"

# Clean up migration jobs/pods (Helm hooks aren't always cleaned up)
echo "Cleaning up migration jobs and pods..."
oc delete job -l app.kubernetes.io/component=migration -n "${NAMESPACE}" 2>/dev/null || true
oc delete pod -l app.kubernetes.io/component=migration -n "${NAMESPACE}" 2>/dev/null || true

# Clean up PVCs (Helm doesn't delete PVCs on uninstall)
echo "Cleaning up PVCs..."
oc delete pvc --all -n "${NAMESPACE}" 2>/dev/null || true

# Optionally delete the project
if [ "${DELETE_PROJECT}" = "true" ]; then
  echo "Deleting project ${NAMESPACE}..."
  oc delete project "${NAMESPACE}" 2>/dev/null || echo "Project not found"
fi

echo ""
echo "=== Undeploy complete ==="
