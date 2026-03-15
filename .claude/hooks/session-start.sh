#!/bin/bash
set -euo pipefail

# Only run in remote (cloud) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# ── Install GitHub CLI ────────────────────────────────────────────────
if ! command -v gh &>/dev/null; then
  apt-get update -qq && apt-get install -y -qq gh >/dev/null
fi

# ── Install Python dependencies ──────────────────────────────────────
cd "$CLAUDE_PROJECT_DIR/backend"
uv sync --frozen 2>/dev/null || uv sync
