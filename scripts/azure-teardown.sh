#!/usr/bin/env bash
# Tear down all Azure infrastructure for budget-tracker.
#
# Deletes the resource group and everything inside it:
#   - Container App (budget-tracker)
#   - Container Apps environment (budget-tracker-env)
#   - Resource group (budget-tracker-rg)
#
# NOTE: This is irreversible. The Neon database is NOT touched.
#
# Usage:
#   ./scripts/azure-teardown.sh
#   ./scripts/azure-teardown.sh --yes   # skip confirmation prompt

set -euo pipefail

RESOURCE_GROUP="budget-tracker-rg"

# ---------------------------------------------------------------------------
# Confirm before destroying
# ---------------------------------------------------------------------------
if [[ "${1:-}" != "--yes" ]]; then
    echo "WARNING: This will permanently delete resource group '${RESOURCE_GROUP}'"
    echo "         and all resources inside it (Container App, environment, etc.)."
    echo "         The Neon database will NOT be affected."
    echo ""
    read -r -p "Type the resource group name to confirm: " confirm
    if [[ "$confirm" != "$RESOURCE_GROUP" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Delete resource group (cascades to all child resources)
# ---------------------------------------------------------------------------
echo ""
echo "==> Deleting resource group: ${RESOURCE_GROUP} ..."
az group delete \
    --name "$RESOURCE_GROUP" \
    --yes \
    --no-wait

echo ""
echo "==> Deletion initiated (running in background on Azure)."
echo "    Track progress: az group show --name ${RESOURCE_GROUP}"
