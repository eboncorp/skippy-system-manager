# Git Workflow with MCP Server

**Use Cases**: Git operations integrated with credential scanning and protocols

**Tools Used**: git_status, git_diff, run_credential_scan, git_log, search_skippy_scripts

**Protocol Integration**: Pre-Commit Sanitization Protocol, Git Workflow Protocol, Script Creation Protocol

---

## Standard Git Workflow

### Step 1: Check Repository Status

**Before starting work**:
```
Check git status for skippy repository
```

**What it shows**:
- Modified files
- Untracked files
- Staged changes
- Current branch
- Commits ahead/behind remote

### Step 2: Review Changes

**Before staging**:
```
Show me the git diff for unstaged changes in skippy
```

**What it shows**:
- Line-by-line changes
- Added/deleted lines
- Modified files

**For staged changes**:
```
Show me the staged changes (cached diff) in skippy
```

### Step 3: Run Credential Scan (REQUIRED)

**Pre-Commit Sanitization Protocol - MANDATORY**:
```
Run credential scan on skippy before I commit
```

**What it scans for**:
- API keys
- Passwords
- Tokens
- AWS credentials
- Private keys
- SSH credentials
- Database passwords
- Email credentials

**Script**: `/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh`

**If scan finds issues**:
- STOP immediately
- Review each finding
- Remove or move credentials to .env
- Re-run scan until clean

### Step 4: Stage and Commit

**Manual terminal commands** (MCP server doesn't auto-commit):
```bash
git add [files]
git commit -m "Descriptive message"
```

### Step 5: Review Commit History

**After committing**:
```
Show me the last 5 commits in skippy
```

**Verify**:
- Commit message is descriptive
- No credential files in commit
- Changes look correct

### Step 6: Push to Remote

**Manual terminal command**:
```bash
git push origin main
```

---

## Pre-Commit Sanitization Protocol

### Full Protocol Flow

**Required before EVERY commit**:

1. **Check status**:
```
Check git status
```

2. **Review all changes**:
```
Show git diff for all unstaged changes
```

3. **Run credential scan**:
```
Run credential scan on skippy
```

4. **Fix any findings**:
   - Remove hardcoded passwords
   - Move API keys to .env
   - Remove test credentials
   - Update .gitignore if needed

5. **Re-scan to verify**:
```
Run credential scan again to verify it's clean
```

6. **Only then commit**:
```bash
git add .
git commit -m "Description"
```

### Example: October 31st API Key Incident

**What happened**: API key accidentally committed to git

**Proper workflow to prevent**:

1. Before committing the API key code:
```
Run credential scan on skippy
```

2. Scan would have found:
```
WARNING: Potential API key found in file.py
  Line 42: ANTHROPIC_API_KEY = "sk-ant-..."
```

3. Fix BEFORE committing:
```python
# Instead of hardcoding:
ANTHROPIC_API_KEY = "sk-ant-..."  # WRONG

# Use environment variable:
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # CORRECT
```

4. Add to .env:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

5. Ensure .env is gitignored:
```bash
echo ".env" >> .gitignore
```

6. Re-scan:
```
Run credential scan again to verify clean
```

7. Now safe to commit

---

## Script Creation Protocol Integration

### Before Creating New Script

**Protocol requires**: Search existing 226+ scripts first

1. **Search for similar scripts**:
```
Search skippy scripts for "backup" keyword
```

2. **Review categories**:
```
List all script categories in skippy
```

3. **Check specific script**:
```
Get info about script: backup_wordpress_v1.0.0.sh
```

4. **Decision**:
   - If script exists: Modify existing version
   - If similar exists: Use as template
   - Only create new if nothing similar

### After Creating New Script

**Git workflow**:

1. **Check status**:
```
Check git status for skippy
```

2. **Review the new script**:
```
Show git diff for the new script
```

3. **Run credential scan**:
```
Run credential scan to verify no hardcoded passwords in new script
```

4. **Commit** (manual):
```bash
git add scripts/category/new_script_v1.0.0.sh
git commit -m "Add new_script_v1.0.0.sh for [purpose]"
```

---

## Common Git Operations

### Check What Changed in Last Commit

```
Show me the last commit in skippy repository
```

**Then review**:
```
Show git diff for that specific commit
```

### Compare Current Work to Remote

```
Check git status to see if ahead/behind remote
```

### Find When Feature Was Added

```
Show git log history to find when [feature] was added
```

**Search in output** for commit message keywords

### Undo Uncommitted Changes

**Manual** (MCP doesn't auto-modify):
```bash
# Undo changes to specific file
git checkout -- filename

# Undo all changes
git reset --hard
```

### Review Changes Before Pull

```bash
# Manual
git fetch origin
git diff main origin/main
```

---

## Workflow Examples

### Example 1: Adding New MCP Tool

**Full workflow**:

1. **Check current state**:
```
Check git status for mcp-servers directory
```

2. **Make changes** (edit server.py)

3. **Review changes**:
```
Show git diff for mcp-servers/general-server/server.py
```

4. **Run credential scan**:
```
Run credential scan on skippy repository
```

5. **If credentials found** (like SSH password):
   - Move to .env file
   - Update code to use .env
   - Add .env to .gitignore

6. **Re-scan to verify clean**:
```
Run credential scan again
```

7. **Commit** (manual):
```bash
git add mcp-servers/general-server/server.py
git commit -m "Add new tool to MCP server v2.1.0"
```

8. **Verify commit**:
```
Show last commit in git log
```

### Example 2: Updating WordPress Scripts

**Full workflow**:

1. **Search for existing WordPress scripts**:
```
Search skippy scripts for "wordpress" keyword
```

2. **Review existing script**:
```
Get info about wordpress_backup_v1.0.0.sh
```

3. **Make changes** (edit or create new version)

4. **Check git status**:
```
Check git status
```

5. **Review changes**:
```
Show git diff for unstaged changes
```

6. **Credential scan**:
```
Run credential scan
```

7. **Fix any database passwords found**

8. **Commit** (manual):
```bash
git add scripts/wordpress/wordpress_backup_v1.1.0.sh
git commit -m "Update WordPress backup script - add database export"
```

### Example 3: Emergency Credential Fix

**If credentials already committed**:

1. **Verify the problem**:
```
Run credential scan to identify what was committed
```

2. **Remove from current code**:
   - Move to .env
   - Update code to use environment variable

3. **Git filter-repo** (manual, DANGEROUS):
```bash
# This rewrites history - coordinate with team first
git filter-repo --path filename_with_credentials --invert-paths
```

4. **Force push** (manual, DANGEROUS):
```bash
git push --force origin main
```

5. **Rotate the credential** (change password/key immediately)

6. **Verify clean**:
```
Run credential scan to verify repository is now clean
```

---

## Safety Checklist

### Before Every Commit

- [ ] Check git status
- [ ] Review git diff
- [ ] Run credential scan
- [ ] Fix any credential findings
- [ ] Re-scan to verify clean
- [ ] Commit with descriptive message
- [ ] Verify commit in git log

### Before Every Push

- [ ] Review last few commits
- [ ] Verify no .env files in commits
- [ ] Verify no backup files in commits
- [ ] Verify credential scan is clean
- [ ] Push to remote

### Weekly Git Hygiene

- [ ] Review all uncommitted changes
- [ ] Clean up old branches
- [ ] Review recent commit history
- [ ] Run credential scan on entire repo
- [ ] Update .gitignore if needed

---

## Natural Language Examples

**Check before commit**:
```
"Check git status and show me what I'm about to commit"
```

**Full pre-commit check**:
```
"Run credential scan and show me git diff before I commit"
```

**Review recent work**:
```
"Show me the last 10 commits in skippy"
```

**Before creating script**:
```
"Search for existing scripts about database backups before I create a new one"
```

**After making changes**:
```
"Show me git diff, then run credential scan to verify safe to commit"
```

---

## Troubleshooting

### Credential Scan Finds False Positive

**Problem**: Scan flags something that's not a real credential

**Solution**: Review the finding carefully
- If it's a placeholder/example: OK to commit
- If it's a test credential: Remove anyway (security hygiene)
- If it's a public key: Usually OK
- If it's a private key: NEVER commit

### Forgot to Run Credential Scan

**Problem**: Already committed without scanning

**Solution**:
```
Run credential scan on skippy NOW
```

If it finds credentials:
- DO NOT PUSH
- Amend the commit or create fix commit
- Remove credentials properly
- Re-scan

### Changes Not Showing in Git Diff

**Problem**: Made changes but diff is empty

**Solution**: Check if files are staged
```
Show git diff for cached (staged) changes
```

---

**Related Tools**:
- `git_status` - Repository status
- `git_diff` - Show changes
- `run_credential_scan` - Security scan
- `git_log` - Commit history
- `search_skippy_scripts` - Find existing scripts
- `get_protocol` - Read Git Workflow Protocol

**Related Protocols**:
- Pre-Commit Sanitization Protocol (MANDATORY)
- Git Workflow Protocol
- Script Creation Protocol

**Related Scripts**:
- `/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh`
