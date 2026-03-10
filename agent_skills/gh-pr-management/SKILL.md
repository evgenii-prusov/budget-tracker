---
name: gh-pr-management
description: Manage GitHub PR feedback by fetching review comments and resolving threads via CLI. Use when Gemini CLI needs to address reviewer comments, find thread IDs using GraphQL, or mark review discussions as resolved.
---

# GitHub PR Management

## Overview

This skill provides a formalized workflow for addressing GitHub PR feedback using the `gh` CLI and GraphQL API. It enables efficient fetching of review threads and programmatic resolution of discussions.

## Workflow

### 1. Fetch Review Context
Start by listing all review threads to identify unresolved feedback and retrieve their unique node IDs.

```bash
# Refer to references/graphql.md for the full query
gh api graphql ...
```

### 2. Analyze and Address Feedback
- Read the comment body from the query results.
- Implement the requested changes in the codebase.
- (Optional) Reply to the thread using `addPullRequestReviewThreadReply` if clarification or confirmation is needed.

### 3. Resolve Threads
Once the changes are implemented and verified, mark the review thread as resolved.

```bash
# Refer to references/graphql.md for the resolve mutation
gh api graphql ...
```

## Detailed Resources

- **GraphQL Queries**: See [references/graphql.md](references/graphql.md) for ready-to-use GraphQL snippets for fetching, replying, and resolving.
- **Workflow Guidance**: Always verify that implementation matches the requested feedback before resolving a thread. Use Plan Mode to systematically address multiple comments.
