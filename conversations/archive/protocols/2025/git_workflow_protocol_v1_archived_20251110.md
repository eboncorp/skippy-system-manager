# Git Workflow Protocol

**Date Created**: 2025-10-28
**Purpose**: Standardized git operations and commit practices
**Applies To**: All git repositories in /home/dave/

## Overview

This protocol defines when and how to use git commands, commit message standards, and branching strategies for projects.

## Core Principles

### Git Safety Rules
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

## Git Commands Process

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

### Commit Process

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

3. **Execute Commit** (parallel when possible):
   ```bash
   # Stage files
   git add file1.md file2.py

   # Create commit
   git commit -m "$(cat <<'EOF'
   [Category] Brief description

   Detailed explanation.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"

   # Verify
   git status
   ```

4. **Push (if requested)**:
   ```bash
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
   git commit -m "Apply pre-commit hook changes"
   ```

## Commit Message Format

### Standard Format

```
[Category] Brief description (max 50 chars)

Detailed explanation of changes (wrap at 72 chars):
- What was changed
- Why it was changed
- Impact of changes

Related files:
- path/to/file1.md
- path/to/file2.py

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Categories

Use these standardized categories:

**Code Changes**:
- `[Feature]` - New features or functionality
- `[Fix]` - Bug fixes
- `[Refactor]` - Code refactoring (no functional changes)
- `[Perf]` - Performance improvements

**Content Changes**:
- `[Content]` - Content updates (policies, pages, posts)
- `[Style]` - CSS/design changes (no functionality change)

**Documentation**:
- `[Docs]` - Documentation updates
- `[README]` - README file updates

**Configuration**:
- `[Config]` - Configuration changes
- `[Deploy]` - Deployment-related changes

**Maintenance**:
- `[Chore]` - Maintenance tasks
- `[Test]` - Adding or updating tests
- `[Build]` - Build system changes
- `[CI]` - CI/CD pipeline changes

**Organization**:
- `[Reorganize]` - File/directory reorganization
- `[Rename]` - Renaming files/directories
- `[Move]` - Moving files/directories

### Category Selection Guidelines

**Multiple categories**: Use most significant one
```
✅ [Feature] Add voter glossary with search
❌ [Feature][Docs] Add voter glossary with search and update README
```

**Unclear category**: Use `[Update]` or ask user

### Examples

#### Good Commit Messages

**Feature Addition**:
```
[Feature] Add voter education glossary v4.0

Integrated comprehensive 499-term glossary with search functionality.

Changes:
- Added louisville_voter_glossary_v4.0_comprehensive.html
- Added louisville_voter_glossary_v4.0_comprehensive.json
- Created WordPress page 328 with iframe integration
- Added glossary notice banners to all policy pages

Impact: Voters can now search and understand government terms with
Louisville-specific context.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Bug Fix**:
```
[Fix] Correct database connection timeout in backup script

Fixed wp db export command hanging indefinitely by adding timeout
parameter and error handling.

Changes:
- backup_wordpress_v1.0.1.sh: Added --timeout=300
- Added connection check before export
- Added error logging to /var/log/backups/

Related: Issue reported on 2025-10-27 where backups would hang.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Content Update**:
```
[Content] Update employee pay plan with union feedback

Incorporated UAW feedback into employee compensation structure.

Changes:
- employee_pay_plan.md: Added progressive wage scale
- Added benefits breakdown table
- Clarified overtime calculation method

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**File Reorganization**:
```
[Reorganize] Convert all filenames to lowercase with underscores

Complete reorganization of 300+ files and 60+ directories for
consistent naming convention.

Changes:
- Renamed all campaign files to lowercase
- Replaced spaces with underscores
- Updated path references in scripts
- Created reorganization documentation

See: /home/dave/reorganization_backup/FILE_REORGANIZATION_SUMMARY.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### Bad Commit Messages

❌ `updated files` - Not descriptive, no category
❌ `fix` - What was fixed?
❌ `WIP` - Work in progress shouldn't be committed
❌ `asdf` - Meaningless
❌ `Fixed the thing that was broken` - No specifics

### Commit Message Template

Use HEREDOC for proper formatting:
```bash
git commit -m "$(cat <<'EOF'
[Category] Brief description

Detailed explanation:
- Point 1
- Point 2
- Point 3

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Branching Strategy

### Repository Types

#### Main Project Repos (rundaverun, skippy)

**Branches**:
- `main` - Production-ready code
- `dev` - Development and testing
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes

**Workflow**:
1. Create feature branch from `dev`
2. Work and commit to feature branch
3. Test thoroughly
4. Merge to `dev`
5. Test in `dev`
6. Merge to `main` when ready for production

**Commands**:
```bash
# Create feature branch
git checkout dev
git pull origin dev
git checkout -b feature/glossary-search

# Work on feature
git add .
git commit -m "..."
git push origin feature/glossary-search

# Merge to dev (after testing)
git checkout dev
git merge feature/glossary-search
git push origin dev

# After dev testing, merge to main
git checkout main
git merge dev
git push origin main
```

#### Simple Projects

**Branches**:
- `main` - Primary branch

**Workflow**:
- Commit directly to main
- Tag releases: `v1.0.0`

### Branch Naming Conventions

**Format**: `type/brief-description`

**Examples**:
- `feature/voter-glossary`
- `fix/database-timeout`
- `docs/setup-instructions`
- `refactor/script-organization`
- `hotfix/security-patch`

**Use lowercase with hyphens** (not underscores)

### When to Create Branches

**Create branch for**:
- New features
- Experimental changes
- Major refactoring
- Long-running work

**Commit to main for**:
- Quick fixes
- Documentation updates
- Minor changes
- Script additions

## Special Cases

### Working with Submodules

If repository has submodules:
```bash
# Update submodules
git submodule update --init --recursive

# Commit submodule changes
cd submodule_directory
git add .
git commit -m "Update submodule"
cd ..
git add submodule_directory
git commit -m "Update submodule reference"
```

### Large Files

**Never commit**:
- Binary files (unless necessary)
- Large media files (>10MB)
- Database dumps (use .gitignore)
- node_modules, venv, __pycache__
- Temporary files
- Log files
- Sensitive credentials

**Use .gitignore**:
```
# Dependencies
node_modules/
venv/
__pycache__/

# Environment
.env
.env.local

# Logs
*.log
logs/

# Database
*.sql
*.db

# Media
*.mp4
*.mov

# Backups
backup_*
*.backup
```

### Sensitive Data

**Before committing**:
1. Check for credentials
2. Check for API keys
3. Check for passwords
4. Check for personal info

**If accidentally committed**:
1. Don't just delete in new commit
2. Use `git filter-branch` or BFG Repo-Cleaner
3. Force push (only if necessary and authorized)
4. Rotate compromised credentials

## Git Status Monitoring

### Check Before Operations

```bash
# Full status check
git status

# Check what's staged
git diff --staged

# Check what's not staged
git diff

# Check untracked files
git ls-files --others --exclude-standard

# Check branch info
git branch -vv
```

### After Operations

```bash
# Verify commit was created
git log -1

# Check current status
git status

# Verify push succeeded
git log origin/main..main  # Should be empty after push
```

## Common Git Operations

### Stage Files

```bash
# Stage specific files
git add file1.md file2.py

# Stage all changes
git add .

# Stage by pattern
git add "*.md"

# Interactive staging
git add -p
```

### Unstage Files

```bash
# Unstage specific file
git restore --staged file.md

# Unstage all
git restore --staged .
```

### Discard Changes

```bash
# Discard changes to file
git restore file.md

# Discard all changes (DANGEROUS - ask first!)
git restore .
```

### View History

```bash
# Recent commits
git log --oneline -10

# With files changed
git log --stat

# Graphical view
git log --graph --oneline --all

# Specific file history
git log --follow -- file.md
```

### View Differences

```bash
# Working directory vs staged
git diff

# Staged vs last commit
git diff --staged

# Between commits
git diff commit1 commit2

# Specific file
git diff file.md
```

## GitHub Integration

### When Using GitHub

**Check GitHub status**:
```bash
# View remote info
git remote -v

# Check tracking
git branch -vv

# Fetch remote changes
git fetch origin
```

### Pull Requests

When user requests PR creation:
1. Push branch to remote
2. Use `gh` CLI if available
3. Or provide GitHub PR URL

```bash
# Create PR with gh CLI
gh pr create --title "Feature: Voter Glossary" --body "Description here"
```

### GitHub Actions

**Monitor CI/CD**:
```bash
# Check runs (if gh CLI available)
gh run list

# View specific run
gh run view <run-id>
```

## Troubleshooting

### Merge Conflicts

When conflicts occur:
1. Alert user
2. Show conflicted files: `git status`
3. Ask how to resolve
4. **Don't automatically resolve** - user decision

### Detached HEAD

If in detached HEAD state:
```bash
# Create branch from current state
git checkout -b recovery-branch

# Or return to main
git checkout main
```

### Accidentally Committed

If wrong files committed:
```bash
# Remove from commit (keep changes)
git reset --soft HEAD~1

# Remove from commit (discard changes) - ASK FIRST
git reset --hard HEAD~1
```

### Push Rejected

If push rejected:
```bash
# Check status
git status

# Fetch and check
git fetch origin
git log origin/main..main

# If behind, pull first
git pull origin main

# Then push
git push origin main
```

## Integration with Claude Workflow

### After Script Creation

When creating scripts in `/home/dave/skippy/scripts/`:
1. Don't automatically commit
2. Wait for user to request commit
3. When user requests commit, include in commit message:
   - Script name and version
   - Purpose
   - Category (automation, backup, etc.)

### After File Reorganization

Large reorganizations:
1. Create comprehensive commit message
2. List major changes
3. Reference documentation
4. Note any breaking changes

### After Content Updates

WordPress/campaign content:
1. Note which pages/posts updated
2. Summarize content changes
3. Include policy names
4. Reference version if applicable

## Quick Reference

### Commit Checklist
- [ ] User explicitly requested commit
- [ ] Ran git status and git diff
- [ ] Reviewed all changes
- [ ] Chose appropriate category
- [ ] Wrote descriptive message
- [ ] Used HEREDOC format
- [ ] Included Co-Authored-By
- [ ] Verified commit created
- [ ] Pushed if requested

### Safe Git Commands
```bash
git status              # Always safe
git log                 # Always safe
git diff                # Always safe
git branch -v           # Always safe
git show                # Always safe
```

### Ask Before Running
```bash
git reset --hard        # DESTRUCTIVE
git push --force        # DESTRUCTIVE
git clean -fd           # DESTRUCTIVE
git checkout .          # DESTRUCTIVE
```

## Best Practices Summary

1. ✅ Only commit when user explicitly requests
2. ✅ Always gather context first (status, diff, log)
3. ✅ Write descriptive commit messages
4. ✅ Use proper categories
5. ✅ Include Co-Authored-By tag
6. ✅ Verify operations succeeded
7. ✅ Never force push without permission
8. ✅ Never skip hooks without permission
9. ✅ Check authorship before amending
10. ✅ Err on side of caution - ask when unsure

---

**This protocol is part of the persistent memory system.**
**Reference when performing any git operations.**
