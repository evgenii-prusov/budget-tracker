#!/usr/bin/env bash
# Build, push, and deploy the budget-tracker image to Azure Container Apps.
#
# Usage:
#   GITHUB_TOKEN=<pat> ./scripts/azure-deploy.sh
#   GITHUB_TOKEN=<pat> TAG=v1.2.3 ./scripts/azure-deploy.sh
#
# Required env vars:
#   GITHUB_TOKEN   — GitHub PAT with write:packages + read:packages scopes
#
# Optional env vars:
#   TAG            — Docker image tag (default: latest)
#
# Prerequisites:
#   - Docker running locally
#   - az CLI installed and logged in (az login)
#   - Infrastructure already provisioned (run scripts/azure-provision.sh first)

set -euo pipefail

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

# Set registry credentials so Container Apps can pull the image
az containerapp registry set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --server "$REGISTRY" \
    --username "$GITHUB_USER" \
    --password "$GITHUB_TOKEN"

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
