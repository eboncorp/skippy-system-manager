# Protocol Branch Workflow

**Version:** 1.0.0
**Last Updated:** 2025-11-10
**Repository:** eboncorp/skippy-system-manager

---

## Branch Structure

### Master Branch
- **Purpose:** Stable, production-ready protocols
- **Protection:** Direct commits discouraged (use PRs from protocols/dev)
- **Content:** Reviewed, tested, and approved protocols only
- **Update Frequency:** When protocols are finalized and reviewed

### Protocols/Dev Branch
- **Purpose:** Active protocol development and updates
- **Protection:** Open for direct commits during development
- **Content:** Work-in-progress protocols, updates, improvements
- **Update Frequency:** Frequent commits during active development

### Feature Branches (Optional)
- **Naming:** `protocol/feature-name` (e.g., `protocol/emergency-rollback`)
- **Purpose:** Major new protocol development
- **Lifecycle:** Created from protocols/dev, merged back to protocols/dev
- **When to Use:** New protocols that need isolated development

---

## Workflow

### 1. Daily Protocol Updates (Small Changes)

**Work directly in protocols/dev:**

```bash
# Ensure you're on protocols/dev
git checkout protocols/dev

# Make your changes to protocols
vim documentation/protocols/some_protocol.md

# Commit changes
git add documentation/protocols/some_protocol.md
git commit -m "Update some_protocol: Brief description of changes"

# Push to GitHub
git push origin protocols/dev
```

### 2. Major Protocol Changes (Requires Review)

**When ready to promote to master:**

```bash
# Ensure protocols/dev is up to date
git checkout protocols/dev
git pull origin protocols/dev

# Review all changes since last master merge
git log master..protocols/dev --oneline

# Switch to master and merge
git checkout master
git merge protocols/dev -m "Merge protocol updates from protocols/dev

Changes:
- List major protocol updates
- Note new protocols added
- Highlight breaking changes

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin master
```

### 3. New Protocol Development (Large Protocols)

**Use feature branches for isolation:**

```bash
# Create feature branch from protocols/dev
git checkout protocols/dev
git checkout -b protocol/new-protocol-name

# Develop the protocol
# ... make changes ...

# Commit progress
git add documentation/protocols/new_protocol.md
git commit -m "Add new protocol: Brief description"

# When complete, merge back to protocols/dev
git checkout protocols/dev
git merge protocol/new-protocol-name -m "Merge protocol/new-protocol-name into protocols/dev"

# Delete feature branch
git branch -d protocol/new-protocol-name

# Push protocols/dev
git push origin protocols/dev
```

---

## Best Practices

### Commit Messages

**Format:**
```
Update protocol_name: Brief description

Details:
- Specific change 1
- Specific change 2

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Examples:**
- `Update wordpress_backup_protocol: Add automated backup verification steps`
- `Add new protocol: Emergency rollback procedures for production incidents`
- `Fix fact_checking_protocol: Correct broken link to external resource`

### Before Merging to Master

**Review Checklist:**
- [ ] All protocols have version numbers
- [ ] All protocols have "Last Updated" dates
- [ ] Protocol cross-references are valid
- [ ] README.md index is updated
- [ ] No work-in-progress or incomplete sections
- [ ] Protocol template requirements met
- [ ] Related protocols reviewed for consistency

### Frequency Guidelines

**protocols/dev commits:** As often as needed (multiple per day is fine)
**master merges:** Weekly or when significant protocol milestone reached
**Feature branches:** For protocols requiring >5 days of development

---

## Branch States

### Current State Indicators

**protocols/dev ahead of master:**
```bash
git checkout protocols/dev
git log master..protocols/dev --oneline
# Shows unreleased protocol updates
```

**Check for conflicts before merge:**
```bash
git checkout master
git merge --no-commit --no-ff protocols/dev
# Preview merge, abort if conflicts
git merge --abort
```

---

## Emergency Fixes

**Hot fix needed in master:**

```bash
# Create hotfix branch from master
git checkout master
git checkout -b hotfix/protocol-critical-fix

# Make urgent fix
vim documentation/protocols/affected_protocol.md

# Commit and merge to master
git commit -am "HOTFIX: Critical correction to protocol X"
git checkout master
git merge hotfix/protocol-critical-fix

# Back-merge to protocols/dev to keep in sync
git checkout protocols/dev
git merge master

# Push both branches
git push origin master
git push origin protocols/dev

# Delete hotfix branch
git branch -d hotfix/protocol-critical-fix
```

---

## GitHub Integration

### Pull Request Template (for large merges)

When creating PR from protocols/dev to master:

```markdown
## Protocol Updates

### New Protocols Added
- [ ] protocol_name_1.md - Brief description
- [ ] protocol_name_2.md - Brief description

### Updated Protocols
- [ ] existing_protocol.md - Changes made

### Breaking Changes
- None / List breaking changes

### Review Checklist
- [ ] All protocols have version numbers
- [ ] All protocols tested
- [ ] README.md updated
- [ ] Cross-references verified

### Related Issues
Closes #XX (if applicable)
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start work on protocol | `git checkout protocols/dev` |
| Create new protocol branch | `git checkout -b protocol/name` |
| Merge protocol to dev | `git checkout protocols/dev && git merge protocol/name` |
| Promote to master | `git checkout master && git merge protocols/dev` |
| Check unreleased updates | `git log master..protocols/dev` |
| Sync dev with master | `git checkout protocols/dev && git merge master` |

---

## Notes

- **Master is stable:** Only merge reviewed, tested protocols
- **Dev is active:** Daily work happens here
- **Feature branches optional:** Use for complex protocols
- **Sync regularly:** Keep protocols/dev in sync with master to avoid conflicts
- **Document all changes:** Good commit messages help future protocol archaeology

---

**Questions?** Check `/home/dave/skippy/documentation/protocols/README.md` for protocol index and guidelines.
