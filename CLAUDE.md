# Project Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Development Methodology
- Follow TDD (Test-Driven Development): write tests first, verify they fail, then write implementation to make them pass.

## Issue Tracking Workflow

### Multi-task features → use an EPIC
When implementing a feature that spans multiple tasks (domain → ORM → service → API → MCP etc.), always:
1. **Create an EPIC first**: `bd create --title="Feature name" --type=epic`
2. **Create sub-tasks** and link them to the EPIC: `bd dep add <task-id> <epic-id>` (task depends on epic being in-progress)
3. **Close sub-tasks** as they are done (after code is committed)
4. **Keep the EPIC open** (`in_progress`) until the PR is merged
5. **Close the EPIC** only after PR merge: `bd close <epic-id> --reason="PR #N merged"`

### Never close tracking before PR merge
- Sub-tasks can be closed when their code is committed and pushed
- The EPIC must remain `in_progress` while the PR is open (CI may fail, review comments may require changes)
- After PR merge: close the EPIC

## Branching Strategy

This project uses a **dev-branch workflow**:

- **`master`** — production branch. Pushes here auto-deploy to Azure. Never commit or PR directly to master (except dev→master release PRs).
- **`dev`** — integration branch. All feature PRs target this branch. CI runs on every push and PR to dev.
- **Feature branches** — created from `dev` via `make branch name=feat/...`. PRs target `dev`.

### Release process
1. Features accumulate in `dev` via merged PRs
2. When ready to release: create a PR from `dev` → `master`
3. Merge the PR → triggers auto-deploy to Azure

### Rules
- Direct commits to both `master` and `dev` are prohibited — always use feature branches + PRs
- PRs target `dev`, not `master` (enforced by PreToolUse hook)
- `make branch` creates branches from `origin/dev`

## Python Execution
- All python commands must be executed via `uv` (e.g., `uv run python`, `uv run pytest`).

## GitHub PR Management
### Resolving Review Comments via CLI
GitHub CLI does not have a native "resolve" command for PR comments, so use the GraphQL API:

1. **Find Thread IDs**:
   ```bash
   gh api graphql -f query='
     query($owner: String!, $repo: String!, $number: Int!) {
       repository(owner: $owner, name: $repo) {
         pullRequest(number: $number) {
           reviewThreads(first: 50) {
             nodes {
               id
               isResolved
               comments(first: 1) { nodes { body } }
             }
           }
         }
       }
     }' -f owner=OWNER -f repo=REPO -F number=PR_NUMBER
   ```

2. **Resolve Thread**:
   ```bash
   gh api graphql -f query='
     mutation($id: ID!) {
       resolveReviewThread(input: { threadId: $id }) {
         thread { isResolved }
       }
     }' -f id=THREAD_NODE_ID
   ```
