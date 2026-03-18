#!/usr/bin/env bash
# Claude Code UserPromptSubmit hook: inject persistent role instructions.
#
# Reads the active role from .claude/.current-role and outputs the
# corresponding role definition file content as additional context.
# This makes the role "sticky" across multiple prompts.
#
# Exit 0 = allow (with optional context injection)

set -euo pipefail

ROLE_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/.current-role"

# No role file = no injection, proceed normally
if [ ! -f "$ROLE_FILE" ]; then
  exit 0
fi

ROLE=$(cat "$ROLE_FILE" 2>/dev/null || echo "")

# Empty or whitespace-only = no injection
if [ -z "${ROLE// /}" ]; then
  exit 0
fi

ROLE_INSTRUCTIONS="${CLAUDE_PROJECT_DIR:-.}/.claude/roles/${ROLE}.md"

# Valid role with existing instructions = inject them
if [ -f "$ROLE_INSTRUCTIONS" ]; then
  echo "[Active Role: ${ROLE}]"
  echo ""
  cat "$ROLE_INSTRUCTIONS"
fi

exit 0
