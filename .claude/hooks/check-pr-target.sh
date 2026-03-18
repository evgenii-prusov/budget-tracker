#!/usr/bin/env bash
# Claude Code PreToolUse hook: block PRs that target master.
# All feature PRs must target 'dev'. Only dev->master release PRs are allowed
# (created manually, not by agents).
#
# Exit 0 = allow, Exit 2 = block with message on stdout.

set -euo pipefail

# Read the Bash tool input from stdin
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "")

# Only inspect gh pr create commands
if ! echo "$CMD" | grep -qE 'gh pr create'; then
  exit 0
fi

# Allow if explicitly targeting dev
if echo "$CMD" | grep -qE '(--base |--base=|-B )dev\b'; then
  exit 0
fi

# Block: either targets master explicitly, or no --base specified
echo "BLOCKED: PRs must target the 'dev' branch, not 'master'."
echo ""
echo "  Use:  gh pr create --base dev ..."
echo ""
echo "  The dev branch is the integration branch. Only dev->master PRs trigger production deploys."
exit 2
