---
description: Complete workflow for developing a new feature from start to finish
---
1. Sync with master branch
// turbo
make sync

2. Create feature branch
// turbo
git checkout -b features/[feature-name]

3. Make code changes
// manual
Edit the necessary files to implement your feature

4. Run quality checks (pre-commit, linting, formatting)
// turbo
make quality

5. Run tests to verify changes
// turbo
make test

6. Generate coverage report (optional)
// turbo
make coverage-html

7. Stage and commit changes (pre-commit hooks run automatically)
// turbo
git add .
git commit -m "feat: [describe your changes]"

8. Push branch to remote
// turbo
git push -u origin features/[feature-name]

9. Create pull request
// manual
Open GitHub and create a pull request from your feature branch to master

10. After PR is merged, switch back to master and sync
// turbo
git checkout master
make sync

11. Delete feature branch (optional cleanup)
// turbo
git branch -d features/[feature-name]
