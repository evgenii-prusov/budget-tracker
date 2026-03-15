#!/usr/bin/env bash
# Build, push, and deploy the budget-tracker image to Azure Container Apps.
#
# Usage:
#   GITHUB_TOKEN=<pat> ./scripts/azure-deploy.sh
#   GITHUB_TOKEN=<pat> TAG=v1.2.3 ./scripts/azure-deploy.sh
#
# Required env vars:
#   GITHUB_TOKEN   — GitHub PAT with write:packages scope (used for docker push).
#                    If GHCR_READ_TOKEN is not set, also needs read:packages (used as pull credential).
#
# Optional env vars:
#   TAG              — Docker image tag (default: latest)
#   GHCR_READ_TOKEN  — GitHub PAT with read:packages scope only, used as the Azure Container Apps
#                      registry pull credential. Defaults to GITHUB_TOKEN if not set. Prefer
#                      supplying a separate read-only PAT so the long-lived Azure credential does
#                      not carry unnecessary write access. Must belong to GHCR_READ_USER.
#   GHCR_READ_USER   — Registry username for the read-only pull credential (default: GITHUB_USER).
#                      Set this if GHCR_READ_TOKEN belongs to a different user (e.g. a machine account).
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
APP_NAME="budget-tracker"
GITHUB_USER="evgenii-prusov"
REGISTRY="ghcr.io"
IMAGE_NAME="${REGISTRY}/${GITHUB_USER}/budget-tracker"
TAG="${TAG:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${TAG}"

# ---------------------------------------------------------------------------
# Authenticate with GitHub Container Registry
# ---------------------------------------------------------------------------
: "${GITHUB_TOKEN:?GITHUB_TOKEN is required — create a PAT with write:packages + read:packages scopes}"

# Use a read-only PAT/user for the Azure pull credential if provided; fall back to GITHUB_TOKEN.
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
docker build --platform linux/amd64 -t "$FULL_IMAGE" ./backend

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
echo "==> Updating container app: ${APP_NAME} (image: ${FULL_IMAGE}) ..."

# Set registry credentials so Container Apps can pull the image.
# GHCR_READ_TOKEN is used here instead of GITHUB_TOKEN: the pull credential is stored
# long-term in Azure and only needs read:packages access, not write:packages.
az containerapp registry set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --server "$REGISTRY" \
    --username "$GHCR_READ_USER" \
    --password "$GHCR_READ_TOKEN"

az containerapp update \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$FULL_IMAGE"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
FQDN=$(az containerapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo ""
echo "==> Deployed successfully!"
echo "    App URL: https://${FQDN}"
