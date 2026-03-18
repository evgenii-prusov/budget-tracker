---
allowed-tools: Read, Glob, Grep, Agent, Bash
---

# Architect Mode

> **Role**: You MUST first read `.claude/roles/architect.md` and follow all constraints defined there throughout this entire interaction.

## Input

$ARGUMENTS

## Step 0: Establish canonical view

Before any analysis, switch to a clean master perspective so your exploration reflects the canonical codebase:

```bash
# Save current branch and any uncommitted work
ORIGINAL_BRANCH=$(git branch --show-current)
if ! git diff-index --quiet HEAD -- || ! git ls-files --others --exclude-standard --quiet; then
  ARCHITECT_STASH_CREATED=1
  git stash push -u -m "architect-stash" >/dev/null
else
  ARCHITECT_STASH_CREATED=0
fi
git checkout master
make sync
```

> **Remember to restore at the end** (Step 5). Only pop the stash if `ARCHITECT_STASH_CREATED=1`.

## Step 1: Gather context

Collect dynamic project state:

```bash
bd ready                                    # Available work
bd list --type=epic --status=in_progress    # Active epics
bd list --status=open                       # All open issues
git branch --show-current                   # Confirm on master
```

If `$ARGUMENTS` contains a beads issue ID (e.g., `beads-xxx`), run `bd show <id>` to load its details.

## Step 2: Explore the codebase

Use **Read**, **Glob**, **Grep**, and **Agent** (with `subagent_type: "Explore"`) to understand:

- Domain model and aggregate boundaries
- Existing service layer and API endpoints
- Test structure and patterns
- Related existing code that the feature touches

Build a mental model of the architecture before designing anything.

## Step 3: Check for duplicates

Before creating issues, search for existing work:

```bash
bd search "<relevant keywords>"
bd list --status=open
```

If similar issues exist, reference them rather than creating duplicates.

## Step 4: Create EPIC and sub-tasks

Follow the project's epic workflow:

1. **Create the EPIC**:
   ```bash
   bd create --title="<Feature name>" --type=epic --priority=2 \
     --description="<Why this feature is needed and what it accomplishes>"
   ```

2. **Create sub-tasks** for each implementation layer, typically:
   - Domain model changes (entities, value objects, business rules)
   - ORM mapping updates
   - Repository methods
   - Service layer functions
   - API endpoints
   - E2E tests (if applicable)

   Each sub-task description **must** include:
   - **What**: Clear scope of changes
   - **Where**: Specific files/modules affected
   - **Tests First**: Describe the test cases to write before implementation
   - **Acceptance criteria**: How to verify the task is done

3. **Link dependencies**:
   ```bash
   bd dep add <task-id> <epic-id>        # task depends on epic
   bd dep add <later-task> <earlier-task> # ordering between tasks
   ```

4. **Mark the EPIC in-progress**:
   ```bash
   bd update <epic-id> --status=in_progress
   ```

## Step 5: Present summary and restore branch

Output a structured summary:

```
## Architecture Plan: <Feature Name>

### EPIC: <id> — <title>

### Sub-tasks (recommended implementation order):
1. <id> — <title> [depends on: <ids>]
2. <id> — <title> [depends on: <ids>]
...

### Dependency graph:
<ASCII or text representation>

### Key design decisions:
- <decision 1 and rationale>
- <decision 2 and rationale>

### Risks / open questions:
- <anything that needs human input>
```

Then restore the original branch:

```bash
git checkout $ORIGINAL_BRANCH
# Only pop if we actually created a stash in Step 0
if [ "$ARCHITECT_STASH_CREATED" = "1" ]; then
  git stash pop
fi
```
