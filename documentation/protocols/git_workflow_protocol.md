# Git Workflow Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Owner**: Skippy Development Team

## Context

This protocol defines the Git workflow for the Skippy System Manager project, ensuring consistent branching, committing, and collaboration practices.

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

# Force push (if already pushed)
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

## Related Protocols

- [Script Saving Protocol](script_saving_protocol.md)
- [Testing Standards Protocol](testing_standards_protocol.md)

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
