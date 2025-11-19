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
