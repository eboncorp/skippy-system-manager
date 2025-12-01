---
description: Manage Git branches, track divergence, and identify merge conflicts
allowed-tools: ["Bash", "Read"]
---

# Git Branch Manager

Summarize branch status, track divergence, identify merge conflicts, and manage feature branches.

## Instructions

When this skill is invoked, provide comprehensive git branch management:

### 1. Identify Repository
Ask the user or detect automatically:
```bash
# Common repositories
RUNDAVERUN_REPO="/home/dave/skippy/work/rundaverun-website"
SKIPPY_REPO="/home/dave/skippy"

# Or current directory
REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null)
```

### 2. Branch Overview
```bash
cd "$REPO_PATH"

# All branches (local and remote)
git branch -a --sort=-committerdate

# Current branch
CURRENT=$(git branch --show-current)
echo "Current branch: $CURRENT"

# Default/main branch
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
echo "Main branch: $MAIN_BRANCH"
```

### 3. Branch Health Summary
```bash
BRANCH_DIR="/home/dave/skippy/work/git/$(date +%Y%m%d_%H%M%S)_branch_analysis"
mkdir -p "$BRANCH_DIR"

cat > "$BRANCH_DIR/BRANCH_REPORT.md" <<EOF
# Git Branch Analysis
**Repository:** $REPO_PATH
**Date:** $(date)
**Current Branch:** $CURRENT

## Branch Status Overview
EOF

# For each branch
for branch in $(git branch --format='%(refname:short)'); do
  echo "### $branch" >> "$BRANCH_DIR/BRANCH_REPORT.md"

  # Last commit
  LAST_COMMIT=$(git log $branch -1 --format='%h %s (%cr)')
  echo "Last commit: $LAST_COMMIT" >> "$BRANCH_DIR/BRANCH_REPORT.md"

  # Commits ahead/behind main
  if [ "$branch" != "$MAIN_BRANCH" ]; then
    AHEAD=$(git rev-list --count $MAIN_BRANCH..$branch)
    BEHIND=$(git rev-list --count $branch..$MAIN_BRANCH)
    echo "Ahead of $MAIN_BRANCH: $AHEAD commits" >> "$BRANCH_DIR/BRANCH_REPORT.md"
    echo "Behind $MAIN_BRANCH: $BEHIND commits" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  fi

  # Remote tracking status
  UPSTREAM=$(git rev-parse --abbrev-ref $branch@{upstream} 2>/dev/null)
  if [ -n "$UPSTREAM" ]; then
    echo "Tracks: $UPSTREAM" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  else
    echo "WARNING: No upstream tracking" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  fi

  echo "" >> "$BRANCH_DIR/BRANCH_REPORT.md"
done
```

### 4. Merge Conflict Detection
```bash
# Check for potential conflicts BEFORE merging
check_merge_conflicts() {
  SOURCE=$1
  TARGET=$2

  # Dry run merge
  git merge-tree $(git merge-base $SOURCE $TARGET) $TARGET $SOURCE > /tmp/merge_test.txt

  if grep -q "^<<<<<<<" /tmp/merge_test.txt; then
    echo "CONFLICTS DETECTED between $SOURCE and $TARGET"
    grep -B5 "^<<<<<<<" /tmp/merge_test.txt
  else
    echo "Clean merge possible from $SOURCE to $TARGET"
  fi
}

# Check main branches
check_merge_conflicts "feature-branch" "master"
```

### 5. Feature Branch Tracking
```bash
# Identify feature branches by pattern
echo "## Feature Branches" >> "$BRANCH_DIR/BRANCH_REPORT.md"

for pattern in "feature/" "claude/" "fix/" "hotfix/"; do
  BRANCHES=$(git branch --list "*$pattern*" --format='%(refname:short)')
  if [ -n "$BRANCHES" ]; then
    echo "### ${pattern}* branches:" >> "$BRANCH_DIR/BRANCH_REPORT.md"
    for b in $BRANCHES; do
      STATUS=$(git log $b -1 --format='%cr - %s')
      echo "- $b: $STATUS" >> "$BRANCH_DIR/BRANCH_REPORT.md"
    done
  fi
done
```

### 6. Stale Branch Detection
```bash
echo "## Stale Branches (>30 days)" >> "$BRANCH_DIR/BRANCH_REPORT.md"

for branch in $(git branch --format='%(refname:short)'); do
  LAST_COMMIT_DATE=$(git log $branch -1 --format='%ci')
  DAYS_OLD=$(( ($(date +%s) - $(date -d "$LAST_COMMIT_DATE" +%s)) / 86400 ))

  if [ $DAYS_OLD -gt 30 ]; then
    echo "- $branch: $DAYS_OLD days old" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  fi
done
```

### 7. Unmerged Commits Analysis
```bash
echo "## Unmerged Work" >> "$BRANCH_DIR/BRANCH_REPORT.md"

for branch in $(git branch --format='%(refname:short)'); do
  if [ "$branch" != "$MAIN_BRANCH" ]; then
    UNMERGED=$(git log $MAIN_BRANCH..$branch --oneline)
    if [ -n "$UNMERGED" ]; then
      echo "### $branch has unmerged commits:" >> "$BRANCH_DIR/BRANCH_REPORT.md"
      echo "$UNMERGED" >> "$BRANCH_DIR/BRANCH_REPORT.md"
      echo "" >> "$BRANCH_DIR/BRANCH_REPORT.md"
    fi
  fi
done
```

### 8. Branch Cleanup Recommendations
```bash
echo "## Cleanup Recommendations" >> "$BRANCH_DIR/BRANCH_REPORT.md"

# Fully merged branches (safe to delete)
MERGED=$(git branch --merged $MAIN_BRANCH | grep -v "^\*\|$MAIN_BRANCH")
if [ -n "$MERGED" ]; then
  echo "### Safe to Delete (fully merged):" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  echo "$MERGED" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  echo "" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  echo "Command: git branch -d <branch-name>" >> "$BRANCH_DIR/BRANCH_REPORT.md"
fi

# Orphaned remote tracking branches
ORPHANED=$(git remote prune origin --dry-run 2>/dev/null)
if [ -n "$ORPHANED" ]; then
  echo "### Orphaned Remote Branches:" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  echo "$ORPHANED" >> "$BRANCH_DIR/BRANCH_REPORT.md"
  echo "Command: git remote prune origin" >> "$BRANCH_DIR/BRANCH_REPORT.md"
fi
```

### 8b. AUTO-CLEANUP (Interactive)
```bash
# Auto-cleanup stale and merged branches
auto_cleanup_branches() {
  REPO_PATH="${1:-.}"
  cd "$REPO_PATH"

  echo "=== Git Branch Auto-Cleanup ==="
  echo "Repository: $(pwd)"
  echo ""

  # Get main branch
  MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
  MAIN_BRANCH="${MAIN_BRANCH:-master}"

  # 1. Prune remote tracking branches
  echo "1. Pruning orphaned remote tracking branches..."
  git remote prune origin

  # 2. Find and delete fully merged local branches
  echo ""
  echo "2. Checking for fully merged local branches..."
  MERGED=$(git branch --merged $MAIN_BRANCH | grep -v "^\*\|$MAIN_BRANCH\|main\|master\|develop")

  if [ -n "$MERGED" ]; then
    echo "Found merged branches:"
    echo "$MERGED"
    echo ""
    echo "Deleting merged branches..."
    echo "$MERGED" | xargs -r git branch -d
  else
    echo "No merged branches to delete."
  fi

  # 3. List stale branches (>60 days) for review
  echo ""
  echo "3. Stale branches (>60 days old):"
  for branch in $(git branch --format='%(refname:short)'); do
    if [ "$branch" != "$MAIN_BRANCH" ] && [ "$branch" != "main" ] && [ "$branch" != "master" ]; then
      LAST_COMMIT_DATE=$(git log "$branch" -1 --format='%ci' 2>/dev/null)
      if [ -n "$LAST_COMMIT_DATE" ]; then
        DAYS_OLD=$(( ($(date +%s) - $(date -d "$LAST_COMMIT_DATE" +%s)) / 86400 ))
        if [ $DAYS_OLD -gt 60 ]; then
          LAST_MSG=$(git log "$branch" -1 --format='%s' | head -c 50)
          echo "  - $branch ($DAYS_OLD days): $LAST_MSG..."
        fi
      fi
    fi
  done

  # 4. Delete stale remote branches (with confirmation)
  echo ""
  echo "4. Checking remote branches..."
  git fetch --prune

  # 5. Summary
  echo ""
  echo "=== Cleanup Complete ==="
  echo "Remaining branches:"
  git branch -a | wc -l
}

# Run auto-cleanup
auto_cleanup_branches "/home/dave/skippy"
```

### 8c. BULK DELETE Stale Branches
```bash
# Delete all branches matching pattern older than N days
bulk_delete_stale() {
  PATTERN="${1:-claude/}"
  MAX_DAYS="${2:-30}"

  echo "Deleting branches matching '$PATTERN' older than $MAX_DAYS days..."

  for branch in $(git branch --format='%(refname:short)' | grep "$PATTERN"); do
    LAST_COMMIT_DATE=$(git log "$branch" -1 --format='%ci' 2>/dev/null)
    if [ -n "$LAST_COMMIT_DATE" ]; then
      DAYS_OLD=$(( ($(date +%s) - $(date -d "$LAST_COMMIT_DATE" +%s)) / 86400 ))
      if [ $DAYS_OLD -gt $MAX_DAYS ]; then
        echo "Deleting $branch ($DAYS_OLD days old)..."
        git branch -D "$branch" 2>/dev/null
        git push origin --delete "$branch" 2>/dev/null || true
      fi
    fi
  done
}

# Example: Delete all claude/* branches older than 14 days
bulk_delete_stale "claude/" 14
```

### 9. Visual Branch Graph
```bash
# Generate visual representation
git log --all --graph --oneline --decorate -20 > "$BRANCH_DIR/branch_graph.txt"

echo "## Branch Graph (last 20 commits)" >> "$BRANCH_DIR/BRANCH_REPORT.md"
echo '```' >> "$BRANCH_DIR/BRANCH_REPORT.md"
cat "$BRANCH_DIR/branch_graph.txt" >> "$BRANCH_DIR/BRANCH_REPORT.md"
echo '```' >> "$BRANCH_DIR/BRANCH_REPORT.md"
```

### 10. Common Operations
```bash
# Create feature branch
git checkout -b feature/new-feature $MAIN_BRANCH

# Update branch with latest main
git checkout feature/my-branch
git rebase $MAIN_BRANCH

# Merge branch (no fast-forward for history)
git checkout $MAIN_BRANCH
git merge --no-ff feature/my-branch

# Delete merged branch
git branch -d feature/my-branch
git push origin --delete feature/my-branch

# Sync with remote
git fetch --all --prune
```

## Usage
- `/git-branches` - Analyze all branches in current or specified repository
- Reports saved to `/home/dave/skippy/work/git/`
- Identifies merge conflicts before they happen
- Tracks feature development across branches
- Recommends cleanup actions

## Best Practices
- Regularly prune stale branches (>30 days old)
- Keep feature branches short-lived
- Rebase on main before merging
- Use meaningful branch names (feature/, fix/, hotfix/)
- Delete branches after merging

## For RunDaveRun Repository
Known branches from previous sessions:
- master (main)
- claude/* branches (AI-generated features)
- feature/* branches (new functionality)
- 8 branches total (as of Nov 12, 2025)
