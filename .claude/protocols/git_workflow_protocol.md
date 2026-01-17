# Git Workflow Protocol

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Branch Structure

| Branch | Purpose | Merge Target |
|--------|---------|--------------|
| `master` | Stable, production-ready | - |
| `develop` | Integration branch | `master` |
| `feature/*` | New features | `develop` |
| `bugfix/*` | Bug fixes | `develop` |
| `hotfix/*` | Urgent production fixes | `master` + `develop` |
| `claude/*` | Claude Code sessions | `develop` |

---

## Daily Development Workflow

### Starting Work
```bash
# Update local branches
git fetch origin

# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/description
```

### During Development
```bash
# Stage changes
git add .

# Commit with semantic message
git commit -m "feat: Add new feature description"

# Push to remote
git push -u origin feature/description
```

### Completing Feature
```bash
# Update with latest develop
git checkout develop
git pull origin develop
git checkout feature/description
git merge develop

# Resolve conflicts if any, then push
git push origin feature/description

# Create PR via GitHub or gh CLI
gh pr create --base develop --title "feat: Description" --body "Details..."
```

---

## Commit Message Convention

```
type(scope): description

[optional body]

[optional footer]
```

### Types
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

### Examples
```bash
git commit -m "feat: Add user authentication"
git commit -m "fix: Resolve login timeout issue"
git commit -m "docs: Update API documentation"
git commit -m "refactor: Simplify database queries"
```

---

## Safety Rules

### NEVER Do Without Explicit Permission
- `git push --force` to any shared branch
- `git reset --hard` on shared branches
- `git commit --amend` after pushing
- Skip hooks with `--no-verify`

### ALWAYS Do
```bash
# Check authorship before amending
git log -1 --format='%an %ae'

# Verify not pushed before amending
git status  # Should show "ahead of origin"

# Use HEREDOC for multi-line commits
git commit -m "$(cat <<'EOF'
feat: Add new feature

Detailed description here.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Hotfix Procedure

For urgent production fixes:

```bash
# Create hotfix from master
git checkout master
git pull origin master
git checkout -b hotfix/critical-fix

# Make fix
git commit -am "fix: Critical fix description"

# Merge to master
git checkout master
git merge hotfix/critical-fix
git push origin master

# Sync back to develop
git checkout develop
git merge master
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-fix
```

---

## Pre-Commit Checks

Before every commit:
1. Run linter (ShellCheck for bash, pylint for Python)
2. Run tests if applicable
3. Check for secrets (automatic via pre-commit hook)
4. Verify file naming conventions

```bash
# Manual pre-commit check
pre-commit run --all-files
```

---

## Merge to Master Protocol

Before merging to master:
- [ ] All tests pass
- [ ] Code review completed
- [ ] No merge conflicts
- [ ] Documentation updated
- [ ] Version numbers updated if applicable

```bash
# Review unreleased changes
git log master..develop --oneline

# Merge when ready
git checkout master
git merge develop -m "Merge develop: Description"
git push origin master
git tag -a v1.x.x -m "Release description"
git push origin --tags
```

---

## Cleanup

```bash
# Delete merged local branches
git branch --merged | grep -v "master\|develop" | xargs git branch -d

# Prune remote tracking branches
git fetch --prune
```

---

## Related

- File Naming Standards Protocol
- Security Incident Protocol
