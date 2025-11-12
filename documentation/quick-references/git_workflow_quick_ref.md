# Git Workflow - Quick Reference

**Protocol:** [Git Workflow Protocol](../protocols/git_workflow_protocol.md)
**Priority:** HIGH
**Use:** Every git commit/push

---

## ⚠️ NEVER DO

1. ❌ Commit without user asking
2. ❌ Force push to main/master
3. ❌ Skip pre-commit hooks
4. ❌ Update git config without asking
5. ❌ Use `git commit --amend` unless specifically requested
6. ❌ Use interactive git commands (`git rebase -i`, `git add -i`)

---

## ✅ Before ANY Git Operation

Run these **in parallel**:
```bash
git status              # See what's changed
git log --oneline -5    # See recent commits
git diff                # See unstaged changes
git diff --staged       # See staged changes
```

---

## 📝 Commit Process

### 1. Stage Files
```bash
git add file1.md file2.py
```

### 2. Create Commit (Use HEREDOC!)
```bash
git commit -m "$(cat <<'EOF'
feat(feature): brief description

Detailed explanation:
- What changed
- Why it changed
- Impact of change

EOF
)"
```

### 3. Verify
```bash
git status
git log -1 --stat
```

### 4. Push (if requested)
```bash
# First time
git push -u origin branch-name

# Subsequent
git push origin branch-name
```

---

## 🏷️ Commit Types

Use conventional commits format:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **style**: Formatting
- **refactor**: Code restructuring
- **test**: Adding tests
- **chore**: Maintenance

### Examples:
```bash
feat(backup): add encryption support
fix(validator): resolve path traversal vulnerability
docs: update README with setup instructions
chore: update dependencies
```

---

## 🌿 Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/add-wordpress-backup` |
| Bug Fix | `bugfix/description` | `bugfix/fix-validation-error` |
| Hotfix | `hotfix/description` | `hotfix/security-patch` |

---

## 🔄 Starting New Work

```bash
# Update main
git checkout main
git pull origin main

# Create branch
git checkout -b feature/my-feature

# Work on changes
# ...

# Commit
git add .
git commit -m "feat: add my feature"

# Push
git push -u origin feature/my-feature
```

---

## 🔧 Pre-commit Hook Failures

If pre-commit hook modifies files:

### Check if safe to amend:
```bash
git log -1 --format='%an %ae'    # Check author (must be you)
git status                        # Check not pushed
```

### If both true (your commit, not pushed):
```bash
git add .
git commit --amend --no-edit
```

### Otherwise (pushed or not your commit):
```bash
git add .
git commit -m "chore: apply pre-commit hook changes"
```

---

## 🔄 Push Retry Logic

If push fails due to network:
```bash
# Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)
for i in {1..4}; do
  git push -u origin branch-name && break
  [ $i -lt 4 ] && sleep $((2 ** i))
done
```

---

## 🚨 Emergency Rollback

### Undo last commit (not pushed):
```bash
git reset --soft HEAD~1    # Keep changes
# or
git reset --hard HEAD~1    # Discard changes
```

### Revert pushed commit:
```bash
git revert HEAD
git push origin branch-name
```

---

## 📋 Commit Checklist

Before committing:
- [ ] Ran `git status` and `git diff`
- [ ] Reviewed all changes
- [ ] No sensitive data (credentials, keys)
- [ ] Tests pass (if applicable)
- [ ] Commit message is clear
- [ ] Using HEREDOC format for multi-line messages
- [ ] User explicitly requested commit

---

## 🔍 Common Issues

### "Your branch has diverged"
```bash
git fetch origin
git rebase origin/main
# Resolve conflicts
git rebase --continue
git push --force-with-lease origin branch-name
```

### "Pre-commit hook failed"
```bash
# Review what failed
# Fix the issues
# Try commit again
# or (if hook is wrong)
git commit --no-verify  # Only if user explicitly requests!
```

---

## 📚 Related Protocols

- **pre_commit_sanitization_protocol** - Security scanning
- **authorization_protocol** - When to ask permission
- **script_saving_protocol** - Saving scripts properly

---

**Full Protocol:** documentation/protocols/git_workflow_protocol.md
**Version:** 2.0.0 (merged and enhanced)
