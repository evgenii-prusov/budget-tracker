#!/usr/bin/env bash
# Claude Code PostToolUse hook: after PR creation, instruct agent to schedule
# a review comment check in 5 minutes.
#
# Fires on Bash tool — only activates when the command contains "gh pr create".

set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "")

# Only trigger on PR creation commands
if ! echo "$CMD" | grep -qE 'gh pr create'; then
  exit 0
fi

echo "ACTION REQUIRED: A PR was just created. Schedule a background agent to fetch and handle review comments in 5 minutes. Use the Agent tool with run_in_background=true. The agent prompt should: sleep 300, then fetch PR comments with gh api, analyze them, implement fixes if needed, push, and resolve threads."
exit 0
