# Contributing to Skippy

Guidelines for maintaining and extending the Skippy system.

---

## Before Creating New Scripts

**CRITICAL:** Always check if similar functionality exists:

```bash
# Search existing scripts
skippy-script search "keyword"

# Check script categories
ls development/scripts/

# Review script details
skippy-script info script_name.sh
```

With 179+ scripts, duplication is the biggest risk. If similar functionality exists, extend that script rather than creating a new one.

---

## File Naming Standards

**All files must follow:**
- Lowercase with underscores (no capitals, no spaces)
- Format: `{purpose}_{specific_task}_v{version}.{ext}`
- Semantic versioning (v1.0.0, v1.1.0, v2.0.0)

**Examples:**
- ✅ `wordpress_backup_v1.0.0.sh`
- ✅ `audit_skills_v1.0.0.py`
- ❌ `WordPress-Backup.sh`
- ❌ `audit_skills.py` (missing version)

---

## Script Header Template

All scripts must include this header:

```bash
#!/bin/bash
# Script Name v1.0.0
# Brief description of what this script does
#
# Usage:
#   script_name [options] arguments
#
# Examples:
#   script_name --option value
#
# Dependencies:
#   - wp-cli
#   - python3
#
# Author: Dave Biggers Campaign
# Created: YYYY-MM-DD
# Last Modified: YYYY-MM-DD
```

---

## Creating New Tools

### 1. Use the Script Manager

```bash
skippy-script create
# Follow prompts for category, name, description
```

### 2. Make Executable

```bash
chmod +x /path/to/script.sh
```

### 3. Add to bin/ if it's a CLI tool

```bash
# Tools in bin/ are available globally
cp script.sh /home/dave/skippy/bin/tool-name
```

### 4. Create Tests

```bash
# Add test to appropriate category
cat > development/tests/automation/test_new_tool.sh
```

### 5. Generate Documentation

```bash
generate-docs
```

### 6. Log Decision

```bash
log-decision
# Explain why this tool was needed
```

---

## Testing Requirements

### All new code must:

1. **Pass ShellCheck** (shell scripts)
```bash
shellcheck script.sh
```

2. **Pass Pylint** (Python scripts)
```bash
pylint script.py
```

3. **Have unit tests**
```bash
# Add test to development/tests/
bash development/tests/run_tests.sh
```

4. **Pass pre-commit hooks**
```bash
# Hooks auto-run on commit
git commit
```

5. **Pass GitHub Actions**
```bash
# Auto-runs on push
git push
```

---

## Pull Request Process

1. **Create feature branch**
```bash
git checkout -b feature/description
```

2. **Make changes following standards**

3. **Test locally**
```bash
bash development/tests/run_tests.sh
health-dashboard
```

4. **Generate documentation**
```bash
generate-docs
generate-changelog
```

5. **Commit with semantic message**
```bash
git commit -m "feat: Add new feature"
# or
git commit -m "fix: Resolve bug"
# or
git commit -m "chore: Update docs"
```

6. **Push and create PR**
```bash
git push origin feature/description
gh pr create
```

7. **GitHub Actions will auto-test**

---

## Commit Message Convention

**Format:** `type: description`

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `chore:` - Maintenance (docs, deps, config)
- `refactor:` - Code restructuring
- `test:` - Add/update tests
- `docs:` - Documentation only

**Examples:**
```
feat: Add WordPress backup automation
fix: Resolve credential scan false positive
chore: Update dependencies to latest versions
test: Add integration tests for runbook generator
docs: Update README with new tool examples
```

---

## Code Quality Standards

### Shell Scripts

- Use ShellCheck and fix all warnings
- Quote all variables: `"$VAR"`
- Use `set -e` for error handling
- Include error messages
- Validate inputs
- Provide help text

### Python Scripts

- Follow PEP 8
- Use type hints
- Include docstrings
- Handle exceptions
- Validate inputs
- Use pathlib for file operations

### All Code

- No hardcoded credentials
- No hardcoded paths (use variables)
- Comprehensive error handling
- Clear variable names
- Comments for complex logic
- Version numbers in headers

---

## Security Requirements

### Never Commit:

- API keys, tokens, passwords
- `.env` files
- Private keys (`.pem`, `.key`)
- Credentials files
- Personal/business documents

### Always:

- Use `.gitignore`
- Run credential scans (pre-commit does this)
- Store secrets in environment variables
- Use read-only permissions where possible

---

## Documentation Standards

### All tools must have:

1. **Header with metadata**
2. **Usage examples**
3. **Dependency list**
4. **Error handling examples**

### Generate docs after changes:

```bash
generate-docs
```

### Create runbooks for workflows:

```bash
generate-runbook "workflow name"
```

---

## Maintenance Schedule

### Daily (Automated)

- Work file cleanup (30 day retention)
- Analytics updates
- Health checks

### Weekly (Manual)

- Review usage analytics
- Update documentation
- Review open issues

### Monthly (Manual)

- Optimize based on analytics
- Archive old sessions
- Update dependencies

---

## Performance Guidelines

### Profile new scripts:

```bash
profile-script new_script.sh
```

### Optimization targets:

- Scripts < 5 seconds for common operations
- No unnecessary file reads
- Cache when appropriate
- Parallel operations where possible

---

## Architecture Decisions

### Document all major decisions:

```bash
log-decision

# Creates ADR (Architecture Decision Record)
# Explains: What, Why, Alternatives, Consequences
```

### Review existing ADRs:

```bash
ls ~/.skippy/adr/
```

---

## Environment Profiles

### When to create new profile:

- New workflow type (currently: wordpress, script-dev, campaign)
- Different tool sets needed
- Specific environment variables required

### Profile template:

```bash
# ~/.skippy/profiles/new-profile.env

# Description of this profile
export PRIMARY_PATH="/path/to/project"
export TOOL_PATH="/path/to/tools"

# Aliases
alias shortcut="long command"

# Functions
function_name() {
    # function body
}
```

---

## Release Process

1. **Update version numbers**
2. **Generate changelog**
```bash
generate-changelog
```

3. **Test everything**
```bash
bash development/tests/run_tests.sh
health-dashboard
```

4. **Create git tag**
```bash
git tag -a v2.1.0 -m "Release 2.1.0"
git push --tags
```

5. **Update README**
6. **Document release notes**

---

## Getting Help

**Before asking:**
1. Check `health-dashboard`
2. Review runbooks: `ls documentation/runbooks/`
3. Search conversations: `ls documentation/conversations/`
4. Check tool help: `tool-name --help`

**When reporting issues:**
- Include error messages
- Include steps to reproduce
- Include environment (which profile)
- Include health-dashboard output

---

**Last Updated:** 2025-11-19  
**Maintainer:** Dave Biggers Campaign Tech Team
