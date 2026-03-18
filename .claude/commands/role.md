# Switch Active Role

Set or clear the persistent agent role for this session.

## Input

$ARGUMENTS

## Instructions

Based on the argument provided:

### If argument is a role name (e.g., `architect`, `dev`):
1. Verify the role file exists at `.claude/roles/<role-name>.md`
2. Write the role name to `.claude/.current-role` (just the name, no path, no newline)
3. Read and display the role file to confirm what role is now active
4. Respond: "Switched to **<role>** mode. All subsequent prompts will follow this role until you run `/role clear`."

### If argument is `clear` or `off`:
1. Delete `.claude/.current-role` if it exists
2. Respond: "Role cleared. Operating in default mode."

### If argument is `list`:
1. List all `.md` files in `.claude/roles/` directory
2. Show which one is currently active (if any)

### If no argument:
1. Check if `.claude/.current-role` exists
2. If yes: read it and respond "Current role: **<role>**"
3. If no: respond "No role active. Use `/role <name>` to set one. Available roles: `architect`, `dev`"
