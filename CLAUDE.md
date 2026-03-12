# Project Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Development Methodology
- Follow TDD (Test-Driven Development): write tests first, verify they fail, then write implementation to make them pass.

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
