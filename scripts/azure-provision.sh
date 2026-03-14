#!/usr/bin/env bash
# One-time Azure infrastructure provisioning for budget-tracker.
#
# Creates:
#   - Resource group
#   - Container Apps environment
#   - Container App (placeholder image; run 'make deploy' after to push the real one)
#
# Usage:
#   ./scripts/azure-provision.sh
#
# Secrets are read from environment variables or backend/.env:
#   DATABASE_URL   — Neon pooled connection string
#   API_KEY        — API authentication key
#   CORS_ORIGINS   — Comma-separated allowed origins (optional, defaults to localhost)
#
# Prerequisites:
#   - az CLI installed and logged in (az login)
#   - 'containerapp' extension: az extension add --name containerapp

set -euo pipefail

RESOURCE_GROUP="budget-tracker-rg"
LOCATION="westeurope"
ENVIRONMENT="budget-tracker-env"
APP_NAME="budget-tracker"
GITHUB_USER="evgenii-prusov"
REGISTRY="ghcr.io"
IMAGE="${REGISTRY}/${GITHUB_USER}/budget-tracker:latest"

# ---------------------------------------------------------------------------
# Load secrets from backend/.env if not already in environment
# ---------------------------------------------------------------------------
if [[ -z "${DATABASE_URL:-}" || -z "${API_KEY:-}" ]]; then
    if [[ -f backend/.env ]]; then
        echo "Loading secrets from backend/.env ..."
        set -a
        # shellcheck disable=SC1091
        source backend/.env
        set +a
    fi
fi

: "${DATABASE_URL:?DATABASE_URL is required — set it in the environment or backend/.env}"
: "${API_KEY:?API_KEY is required — set it in the environment or backend/.env}"

CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:5173}"

# ---------------------------------------------------------------------------
# Register provider (idempotent)
# ---------------------------------------------------------------------------
echo ""
echo "==> Registering Microsoft.App provider ..."
az provider register --namespace Microsoft.App --wait

# ---------------------------------------------------------------------------
# Resource group
# ---------------------------------------------------------------------------
echo ""
echo "==> Creating resource group: $RESOURCE_GROUP (location: $LOCATION) ..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION"

# ---------------------------------------------------------------------------
# Container Apps environment
# ---------------------------------------------------------------------------
echo ""
echo "==> Creating Container Apps environment: $ENVIRONMENT ..."
az containerapp env create \
    --name "$ENVIRONMENT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION"

# ---------------------------------------------------------------------------
# Container App
# A placeholder image is used here; run 'make deploy' to push the real image.
# Replicas: min=0 (scale to zero when idle) max=1 (stay on free tier).
# ---------------------------------------------------------------------------
echo ""
echo "==> Creating container app: $APP_NAME ..."
az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENVIRONMENT" \
    --image "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 1 \
    --cpu 0.25 \
    --memory 0.5Gi \
    --secrets \
        "database-url=${DATABASE_URL}" \
        "api-key=${API_KEY}" \
    --env-vars \
        "DATABASE_URL=secretref:database-url" \
        "API_KEY=secretref:api-key" \
        "CORS_ORIGINS=${CORS_ORIGINS}"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
FQDN=$(az containerapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo ""
echo "==> Infrastructure provisioned successfully."
echo "    App URL (placeholder): https://${FQDN}"
echo ""
echo "Next steps:"
echo "  1. Set GITHUB_TOKEN (PAT with write:packages + read:packages scopes)"
echo "  2. Run: make deploy"
