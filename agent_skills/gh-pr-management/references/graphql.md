# GitHub GraphQL Queries for PR Management

Use these queries with `gh api graphql`.

## Find Review Threads

Use this to get thread IDs, resolution status, and the first comment body for a PR.

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

## Resolve a Review Thread

Use the `id` from the previous query to resolve a specific thread.

```bash
gh api graphql -f query='
  mutation($id: ID!) {
    resolveReviewThread(input: { threadId: $id }) {
      thread { isResolved }
    }
  }' -f id=THREAD_NODE_ID
```

## Reply to a Comment (Optional)

If you need to reply before resolving, use `addPullRequestReviewThreadReply`.

```bash
gh api graphql -f query='
  mutation($threadId: ID!, $body: String!) {
    addPullRequestReviewThreadReply(input: { pullRequestReviewThreadId: $threadId, body: $body }) {
      comment { body }
    }
  }' -f threadId=THREAD_NODE_ID -f body="Your reply message"
```
