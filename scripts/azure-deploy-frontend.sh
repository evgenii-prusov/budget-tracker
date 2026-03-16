#!/usr/bin/env bash
# Build, push, and deploy the budget-tracker-web (frontend) image to Azure Container Apps.
#
# Usage:
#   GITHUB_TOKEN=<pat> ./scripts/azure-deploy-frontend.sh
#   GITHUB_TOKEN=<pat> TAG=v1.2.3 ./scripts/azure-deploy-frontend.sh
#
# Required env vars:
#   GITHUB_TOKEN   — GitHub PAT with write:packages scope (used for docker push).
#                    If GHCR_READ_TOKEN is not set, also needs read:packages (used as pull credential).
#
# Optional env vars:
#   TAG              — Docker image tag (default: latest)
#   GHCR_READ_TOKEN  — Read-only PAT for Azure pull credential (defaults to GITHUB_TOKEN).
#   GHCR_READ_USER   — Registry username for the read-only pull credential (default: GITHUB_USER).
#
# Prerequisites:
#   - Docker running locally
#   - az CLI installed and logged in (az login)
#   - Infrastructure already provisioned (run scripts/azure-provision.sh first)

set -euo pipefail

# Load .env files (env vars take priority over file values)
load_env() {
    local file="$1"
    if [[ -f "$file" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "$file"
        set +a
    fi
}
load_env "backend/.env"
load_env ".env"

RESOURCE_GROUP="budget-tracker-rg"
FRONTEND_APP="budget-tracker-web"
GITHUB_USER="evgenii-prusov"
REGISTRY="ghcr.io"
IMAGE_NAME="${REGISTRY}/${GITHUB_USER}/budget-tracker-web"
TAG="${TAG:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${TAG}"

# ---------------------------------------------------------------------------
# Authenticate with GitHub Container Registry
# ---------------------------------------------------------------------------
: "${GITHUB_TOKEN:?GITHUB_TOKEN is required — create a PAT with write:packages + read:packages scopes}"

GHCR_READ_TOKEN="${GHCR_READ_TOKEN:-$GITHUB_TOKEN}"
GHCR_READ_USER="${GHCR_READ_USER:-$GITHUB_USER}"

echo ""
echo "==> Logging in to ${REGISTRY} ..."
echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$GITHUB_USER" --password-stdin

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
echo ""
echo "==> Building image: ${FULL_IMAGE} ..."
docker build --platform linux/amd64 -t "$FULL_IMAGE" ./frontend

# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------
echo ""
echo "==> Pushing image to ${REGISTRY} ..."
docker push "$FULL_IMAGE"

# ---------------------------------------------------------------------------
# Update container app
# ---------------------------------------------------------------------------
echo ""
echo "==> Updating container app: ${FRONTEND_APP} (image: ${FULL_IMAGE}) ..."

az containerapp registry set \
    --name "$FRONTEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --server "$REGISTRY" \
    --username "$GHCR_READ_USER" \
    --password "$GHCR_READ_TOKEN"

az containerapp update \
    --name "$FRONTEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$FULL_IMAGE"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
FQDN=$(az containerapp show \
    --name "$FRONTEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo ""
echo "==> Frontend deployed successfully!"
echo "    App URL: https://${FQDN}"
