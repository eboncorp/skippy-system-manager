# Git Workflow Protocol

**Version**: 2.0.0
**Last Updated**: 2025-11-10
**Owner**: Skippy Development Team
**Previous Version**: Merged from conversations/git_workflow_protocol.md (v1) and documentation/protocols/git_workflow_protocol.md (v1.0.0)

## Context

This protocol defines the Git workflow for the Skippy System Manager project, ensuring consistent branching, committing, and collaboration practices while maintaining strict safety standards.

## Git Safety Rules ⚠️ CRITICAL

1. ✅ **NEVER** update git config without explicit user request
2. ✅ **NEVER** run destructive git commands (push --force, hard reset) unless explicitly requested
3. ✅ **NEVER** skip hooks (--no-verify, --no-gpg-sign) unless explicitly requested
4. ✅ **NEVER** force push to main/master - warn user if they request it
5. ✅ **AVOID** git commit --amend except when:
   - User explicitly requests amend
   - Adding edits from pre-commit hook
6. ✅ **ALWAYS** check authorship before amending: `git log -1 --format='%an %ae'`
7. ✅ **NEVER** commit changes unless user explicitly asks

## When to Commit

### Always Ask First

When unclear whether to commit, **ask the user first**.

### Commit When User Says

- "commit this"
- "save to git"
- "create a commit"
- "commit these changes"
- "push this"
- After completing task and user says "commit it"

### Never Commit Without Permission

- Don't be proactive with commits
- Don't assume user wants changes committed
- Don't commit just because changes are ready
- **User MUST explicitly request commit**

## Guidelines

1. **Never commit to main directly** - Always use branches
2. **Use descriptive commit messages** - Follow conventional commits
3. **Keep commits atomic** - One logical change per commit
4. **Test before committing** - Ensure code works
5. **Review before merging** - All PRs require review

## Branching Strategy

### Branch Types

```
main
 ├── develop
 ├── feature/feature-name
 ├── bugfix/bug-description
 ├── hotfix/critical-fix
 └── release/v1.2.0
```

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<description>` | `feature/add-backup-encryption` |
| Bug Fix | `bugfix/<description>` | `bugfix/fix-path-validation` |
| Hotfix | `hotfix/<description>` | `hotfix/critical-security-patch` |
| Release | `release/v<version>` | `release/v2.1.0` |

## Commit Message Format

### Convention

Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvement
- `ci`: CI/CD changes

### Alternative Format (With Attribution)

For Claude Code commits, you may use:

```
[Category] Brief description (max 50 chars)

Detailed explanation of changes (wrap at 72 chars):
- What was changed
- Why it was changed
- Impact of changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Examples

```bash
feat(backup): add encryption support for backups

Implemented GPG encryption for backup files to enhance security.

Closes #123
```

```bash
fix(validator): resolve path traversal vulnerability

Added additional path validation checks to prevent directory traversal attacks.
```

```bash
docs: update README with Docker instructions
```

## Commit Process (Detailed)

### Before Any Git Operation

**Run in parallel** (single message, multiple tool calls):

```bash
# Check status
git status

# Check recent commits for style
git log --oneline -5

# Check what will be committed
git diff
git diff --staged
```

### Step-by-Step Commit Procedure

1. **Parallel Information Gathering**:
   ```bash
   git status              # See untracked/modified files
   git diff                # See unstaged changes
   git diff --staged       # See staged changes
   git log --oneline -5    # See recent commit style
   ```

2. **Analyze Changes**:
   - Review all changes being committed
   - Understand the nature of changes
   - Draft appropriate commit message

3. **Execute Commit**:
   ```bash
   # Stage files
   git add file1.md file2.py

   # Create commit with HEREDOC for proper formatting
   git commit -m "$(cat <<'EOF'
   feat(feature): add new capability

   Detailed explanation of what changed and why.

   EOF
   )"

   # Verify
   git status
   ```

4. **Push (if requested)**:
   ```bash
   # First time pushing branch
   git push -u origin branch-name

   # Subsequent pushes
   git push origin branch-name
   ```

### Pre-commit Hook Failures

If commit fails due to pre-commit hook modifying files:

1. **Check if safe to amend**:
   ```bash
   git log -1 --format='%an %ae'           # Check author
   git status | grep "Your branch is ahead" # Check not pushed
   ```

2. **If both true**: Amend the commit
   ```bash
   git add .
   git commit --amend --no-edit
   ```

3. **If either false**: Create new commit
   ```bash
   git add .
   git commit -m "chore: apply pre-commit hook changes"
   ```

## Workflow Procedures

### Starting New Work

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ...

# Commit changes
git add .
git commit -m "feat: add my feature"

# Push to remote
git push -u origin feature/my-feature
```

### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/my-feature
   ```

2. **Open PR on GitHub**
   - Use the PR template
   - Fill in all sections
   - Link related issues

3. **Request review**
   - Assign reviewers
   - Address feedback
   - Make requested changes

4. **Merge when approved**
   - Squash and merge (preferred)
   - Delete branch after merge

### Keeping Branch Updated

```bash
# Fetch latest changes
git fetch origin

# Rebase on main
git checkout feature/my-feature
git rebase origin/main

# Resolve conflicts if any
# Then continue
git rebase --continue

# Force push (if already pushed) - use with caution!
git push --force-with-lease origin feature/my-feature
```

## Code Review

### For Authors

- ✅ Self-review before submitting
- ✅ Test thoroughly
- ✅ Update documentation
- ✅ Respond to feedback promptly
- ✅ Keep PR scope focused

### For Reviewers

- ✅ Review within 24-48 hours
- ✅ Be constructive
- ✅ Focus on code quality
- ✅ Check tests and docs
- ✅ Approve or request changes clearly

## Git Push Retry Logic

For network issues during push:

```bash
# Retry up to 4 times with exponential backoff
# Wait times: 2s, 4s, 8s, 16s

# Example retry logic (automated in CI/CD):
for i in {1..4}; do
  git push -u origin branch-name && break
  [ $i -lt 4 ] && sleep $((2 ** i))
done
```

## Git Fetch/Pull Best Practices

```bash
# Prefer fetching specific branches
git fetch origin branch-name

# For pulls use
git pull origin branch-name

# Apply same retry logic if network failures occur
```

## NEVER Use Interactive Git Commands

**IMPORTANT:** Never use interactive git commands in automated environments:

- ❌ `git rebase -i` (interactive rebase)
- ❌ `git add -i` (interactive add)
- ❌ `git add -p` (patch mode)

These require interactive input which is not supported in automation.

## Related Protocols

- [Script Saving Protocol](script_saving_protocol.md)
- [Pre-commit Sanitization Protocol](../../conversations/pre_commit_sanitization_protocol.md)
- [Authorization Protocol](../../conversations/authorization_protocol.md)

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

---

**Version History:**
- v2.0.0 (2025-11-10): Merged two protocol versions, added safety rules and detailed commit process
- v1.0.0 (2025-11-05): Initial documentation/protocols version
- v1 (2025-10-28): Initial conversations version with safety focus
