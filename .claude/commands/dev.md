# Developer Mode

> **Role**: You MUST first read `.claude/roles/dev.md` and follow all constraints defined there throughout this entire interaction.

## Input

$ARGUMENTS

## Step 1: Select work

If `$ARGUMENTS` contains a beads issue ID, use that. Otherwise, find available work:

```bash
bd ready
```

Pick a task (prefer ones with no blockers). Load its details:

```bash
bd show <id>
```

Claim it:

```bash
bd update <id> --status=in_progress
```

If the task belongs to an EPIC, check the EPIC's status and ensure prerequisite tasks are done:

```bash
bd show <epic-id>
```

## Step 2: Create feature branch

Always branch from origin/master using the Makefile target:

```bash
make branch name=feat/<short-description>
```

**Never** use `git checkout -b` directly (the PreToolUse hook will block it).

## Step 3: Implement with strict TDD

For each layer of the task (domain → service → API):

### 3a. Write the failing test FIRST

- Read the task description's "Tests First" section for guidance
- Write the test in the appropriate test file
- Use existing test patterns and fixtures from the codebase

### 3b. Run to confirm failure

```bash
make test V=1
```

The test **must fail**. If it passes, the test isn't testing new behavior.

### 3c. Write minimal implementation

Implement just enough to make the test pass. Follow existing patterns.

### 3d. Run to confirm pass

```bash
make test V=1
```

### 3e. Refactor if needed

Clean up while keeping tests green.

## Step 4: Commit and push

Stage specific files (never `git add .` or `git add -A`):

```bash
git add backend/app/domain/model.py backend/tests/unit/test_model.py
git commit -m "feat: add <description>"
```

Push and create PR:

```bash
git push -u origin $(git branch --show-current)
gh pr create --title "<Short title>" --body "$(cat <<'EOF'
## Summary
- <bullet points>

## Test plan
- [ ] Unit tests pass
- [ ] Integration tests pass

Closes beads-xxx
EOF
)"
```

## Step 5: Close sub-tasks, keep EPIC open

After commit and push:

```bash
bd close <task-id>
```

**Do NOT close the EPIC** — it stays `in_progress` until the PR is merged.

## PR Review Loop

After PR creation, the PostToolUse hook will remind you to schedule a background review agent. Follow its instructions:

1. Spawn a background agent that sleeps 5 minutes
2. The agent fetches PR comments via `gh api`
3. Analyzes review feedback
4. Implements fixes if needed
5. Pushes and resolves threads via GraphQL API
