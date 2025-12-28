---
description: Complete workflow for developing and submitting a feature
---

## 1. Sync with master
```bash
git checkout master
git pull --rebase origin master
```

## 2. Create feature branch
```bash
git checkout -b feat/descriptive-branch-name
```

## 3. Make code changes
- Implement the feature or fix
- Follow existing code patterns and style

## 4. Run quality checks
```bash
make quality
```
This runs: ruff check, ruff format, pytest, ty check

## 5. Commit changes
```bash
git add <files>
git commit -m "feat: one-line descriptive message"
```
Pre-commit hooks will run automatically.

## 6. Push and create PR
```bash
git push -u origin feat/descriptive-branch-name
gh pr create --title "feat: descriptive title" --body "## Summary
- Change 1
- Change 2

## Test plan
- [x] Tests pass
- [x] Quality checks pass"
```

## 7. Cleanup after merge
```bash
git checkout master
git pull --rebase origin master
git branch -D feat/descriptive-branch-name
```
