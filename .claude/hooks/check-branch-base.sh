#!/usr/bin/env bash
# Claude Code PreToolUse hook: block raw branch creation commands.
# Forces the agent to use "make branch name=..." instead.
#
# Exit 0 = allow, Exit 2 = block with message on stdout.

set -euo pipefail

# Read the Bash tool input from stdin
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "")

# Only inspect branch-creation commands
if ! echo "$CMD" | grep -qE 'git (checkout -b|checkout -B|switch -c) '; then
  exit 0
fi

# Allow if the command is part of "make branch" (Makefile handles it correctly)
if echo "$CMD" | grep -qE '^make branch '; then
  exit 0
fi

# Block with helpful message
echo "BLOCKED: Do not use 'git checkout -b' directly."
echo ""
echo "  Use:  make branch name=fix/my-feature"
echo ""
echo "  This fetches origin and branches from origin/dev automatically."
exit 2
