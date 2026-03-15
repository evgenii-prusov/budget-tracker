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
# Secrets are loaded in priority order:
#   1. Environment variables (highest priority)
#   2. .env  (project root — GITHUB_TOKEN, API_KEY, etc.)
#   3. backend/.env  (DATABASE_URL, app runtime config)
#
# Variables used:
#   DATABASE_URL              — Neon pooled connection string
#   API_KEY                   — REST API authentication key (MCP uses OAuth instead)
#   CORS_ORIGINS              — Comma-separated allowed origins (optional, defaults to localhost)
#   OAUTH_OWNER_PASSWORD_HASH — bcrypt hash of owner password for MCP OAuth login
#   MCP_BASE_URL              — Full public URL of MCP endpoint (auto-derived if not set)
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
# Load secrets: root .env first, then backend/.env (env vars take priority)
# ---------------------------------------------------------------------------
load_env() {
    local file="$1"
    if [[ -f "$file" ]]; then
        echo "Loading $file ..."
        set -a
        # shellcheck disable=SC1090
        source "$file"
        set +a
    fi
}

# Load in reverse priority so higher-priority sources win on re-export
load_env "backend/.env"   # lowest priority: app runtime defaults
load_env ".env"           # higher priority: deploy-time secrets (API_KEY, GITHUB_TOKEN)

: "${DATABASE_URL:?DATABASE_URL is required — add it to .env or backend/.env}"
: "${API_KEY:?API_KEY is required — add it to .env or backend/.env}"
: "${OAUTH_OWNER_PASSWORD_HASH:?OAUTH_OWNER_PASSWORD_HASH is required — generate with: python -c \"import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())\"}"

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

# Write the container app configuration to a temp file so that secrets are
# never exposed as CLI arguments (visible in `ps aux` and az CLI telemetry).
APP_CONFIG=$(mktemp)
trap 'rm -f "$APP_CONFIG"' EXIT

cat > "$APP_CONFIG" <<EOF
properties:
  configuration:
    ingress:
      external: true
      targetPort: 8000
    secrets:
      - name: database-url
        value: "${DATABASE_URL}"
      - name: api-key
        value: "${API_KEY}"
      - name: oauth-owner-password-hash
        value: "${OAUTH_OWNER_PASSWORD_HASH}"
  template:
    containers:
      - image: mcr.microsoft.com/azuredocs/containerapps-helloworld:latest
        name: budget-tracker
        resources:
          cpu: 0.25
          memory: 0.5Gi
        env:
          - name: DATABASE_URL
            secretRef: database-url
          - name: API_KEY
            secretRef: api-key
          - name: OAUTH_OWNER_PASSWORD_HASH
            secretRef: oauth-owner-password-hash
          - name: CORS_ORIGINS
            value: "${CORS_ORIGINS}"
    scale:
      minReplicas: 0
      maxReplicas: 1
EOF

az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENVIRONMENT" \
    --yaml "$APP_CONFIG"

# ---------------------------------------------------------------------------
# Set MCP_BASE_URL (derived from the provisioned FQDN)
# ---------------------------------------------------------------------------
FQDN=$(az containerapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

MCP_BASE_URL="${MCP_BASE_URL:-https://${FQDN}/mcp}"

echo ""
echo "==> Setting MCP_BASE_URL=${MCP_BASE_URL} ..."
az containerapp update \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --set-env-vars "MCP_BASE_URL=${MCP_BASE_URL}"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "==> Infrastructure provisioned successfully."
echo "    App URL (placeholder): https://${FQDN}"
echo "    MCP OAuth: ${MCP_BASE_URL}"
echo ""
echo "Next steps:"
echo "  1. Set GITHUB_TOKEN (PAT with write:packages + read:packages scopes)"
echo "  2. Run: make deploy"
