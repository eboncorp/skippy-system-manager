# Pre-Commit Sanitization Protocol

**Version:** 1.0.0
**Created:** 2025-10-31
**Last Updated:** 2025-11-10
**Purpose:** Prevent credentials and sensitive data from being committed to Git
**Priority:** CRITICAL - MUST follow before EVERY commit
**Trigger Event:** Oct 31, 2025 - Anthropic API key exposed on GitHub

---

## Purpose

This protocol ensures:
- Zero credentials committed to Git repositories (API keys, tokens, passwords)
- Automated pre-commit scanning for sensitive data
- Comprehensive .gitignore patterns for credential files
- Emergency response procedures for exposed credentials
- Secure credential storage best practices

---

## Overview

This protocol ensures that NO sensitive data (API keys, tokens, passwords, credentials) is ever committed to Git repositories. It implements a multi-layer defense system to catch credentials before they reach GitHub.

**Key Principle:** Never trust manual review - automate credential detection.

---

## Incident That Created This Protocol

**Date:** October 31, 2025 at 17:51 UTC
**Event:** Anthropic API key exposed in commit `a50322a` to `eboncorp/skippy-system-manager`
**File:** `google_drive/Claude/api key.odt`
**Impact:** API key automatically revoked by Anthropic
**Additional Exposure:** 3 more credential files found in same commit:
- `github/Nexus(claasic token).odt` (GitHub token)
- `github/nexus github token.odt` (GitHub token)
- `scripts/Utility/NexusController/security.key` (unknown credential)

**Root Cause:** No automated scanning before commit
**Resolution:** Emergency Git history rewrite, all credentials removed

---

## Mandatory Pre-Commit Checklist

### NEVER Skip This Checklist Before ANY Commit

Before running `git add` or `git commit`, you MUST complete ALL steps:

```bash
# Step 1: Review what you're about to add
git status

# Step 2: Run automated credential scan
/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh

# Step 3: Review diff for any sensitive data
git diff --cached

# Step 4: Only if scan passes, proceed with commit
git commit -m "message"
```

---

## Automated Pre-Commit Hook

### Installation

The pre-commit hook is automatically installed in `.git/hooks/pre-commit` and runs before every commit.

**Location:** `/home/dave/skippy/.git/hooks/pre-commit`

**What it does:**
1. Scans all staged files for credential patterns
2. Checks filenames against blacklist patterns
3. Searches file contents for API keys, tokens, passwords
4. BLOCKS commit if credentials detected
5. Shows which files/patterns failed

**Override:** Only if you're 100% certain it's a false positive:
```bash
git commit --no-verify -m "message"
```

⚠️ **WARNING:** Using `--no-verify` bypasses all safety checks. Only use in emergencies.

---

## Credential Detection Patterns

### Filename Patterns (HIGH RISK)

Files matching these patterns are ALWAYS blocked:

```
*api*key*
*apikey*
*.key (except *.keyring, *.keyboard)
*.pem
*.p12
*.pfx
*token*
*secret*
*credential*
*password*
*.env
.env.*
id_rsa
id_dsa
id_ecdsa
id_ed25519
*.ppk
*.crt
*.cer
*.der
```

### Content Patterns (API Keys)

File contents matching these patterns trigger warnings:

```regex
# API Keys
sk-[a-zA-Z0-9]{32,}              # Anthropic API keys
ghp_[a-zA-Z0-9]{36,}             # GitHub Personal Access Tokens
gho_[a-zA-Z0-9]{36,}             # GitHub OAuth tokens
AKIA[0-9A-Z]{16}                 # AWS Access Key ID
AIza[0-9A-Za-z-_]{35}            # Google API Key
sk_live_[0-9a-zA-Z]{24,}         # Stripe API Key
sk_test_[0-9a-zA-Z]{24,}         # Stripe Test Key
sq0atp-[0-9A-Za-z\-_]{22}        # Square Access Token
access_token.*['"][0-9a-zA-Z]{32,}['"]  # Generic OAuth tokens
api[_-]?key.*['"][0-9a-zA-Z]{20,}['"]   # Generic API keys
```

### Sensitive Directories

These directories are ALWAYS excluded from commits:

```
credentials/
secrets/
.secrets/
.aws/
.azure/
.gcp/
.anthropic/
google_drive/Claude/
github/*.odt
```

---

## Pre-Commit Security Scan Script

**Location:** `/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh`

**Usage:**
```bash
# Manual scan before commit
./scripts/utility/pre_commit_security_scan_v1.0.0.sh

# Or run from anywhere
/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh

# Scan specific files
./scripts/utility/pre_commit_security_scan_v1.0.0.sh file1.txt file2.py
```

**Features:**
- Scans staged files for credentials
- Pattern matching for common API key formats
- Filename blacklist checking
- Directory blacklist checking
- Colored output (red = danger, green = safe)
- Exit code 1 if credentials found (blocks commit)
- Exit code 0 if safe (allows commit)

---

## Git Hook Integration

### Pre-Commit Hook

**File:** `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Pre-commit hook: Block commits containing credentials
# Created: 2025-10-31
# Trigger: Anthropic API key exposure incident

echo "🔍 Running security scan before commit..."

# Run the security scan script
/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh

# Capture exit code
SCAN_RESULT=$?

if [ $SCAN_RESULT -ne 0 ]; then
    echo ""
    echo "❌ COMMIT BLOCKED: Potential credentials detected!"
    echo ""
    echo "Actions you can take:"
    echo "1. Remove the flagged files from staging: git reset HEAD <file>"
    echo "2. Add to .gitignore: echo '<pattern>' >> .gitignore"
    echo "3. Review file contents and remove credentials"
    echo "4. If false positive, override: git commit --no-verify"
    echo ""
    exit 1
fi

echo "✅ Security scan passed. Proceeding with commit."
exit 0
```

**Installation:**
```bash
chmod +x /home/dave/skippy/.git/hooks/pre-commit
```

---

## Emergency Response Plan

### If Credentials Are Committed Locally (Before Push)

**IMMEDIATE ACTION:**
```bash
# 1. Abort the commit
git reset --soft HEAD~1

# 2. Remove sensitive files
git reset HEAD <sensitive-file>

# 3. Add to .gitignore
echo "<sensitive-file>" >> .gitignore

# 4. Re-commit without sensitive files
git add .
git commit -m "message"
```

### If Credentials Are Pushed to GitHub

**CRITICAL - ASSUME COMPROMISED:**

1. **Revoke credentials IMMEDIATELY** (within 5 minutes)
   - Anthropic: https://platform.claude.com/settings/keys
   - GitHub: https://github.com/settings/tokens
   - AWS: https://console.aws.amazon.com/iam/

2. **Remove from Git history** (MUST be done):
   ```bash
   # Install git-filter-repo
   sudo apt-get install git-filter-repo

   # Remove file from all commits
   git filter-repo --invert-paths --path <sensitive-file> --force

   # Force push to rewrite GitHub history
   git push origin --force --all
   ```

3. **Verify removal on GitHub:**
   - Check repository files
   - Check commit history
   - Search for key patterns in GitHub search

4. **Generate new credentials**
   - Create replacement keys
   - Update local configuration
   - Update production systems
   - Document what was changed

5. **Create incident report** in `/home/dave/skippy/conversations/error_logs/`

---

## .gitignore Patterns

Comprehensive `.gitignore` has been implemented with these sections:

### Critical Patterns
```gitignore
# API Keys and Tokens
*api*key*
*apikey*
*.key
*.pem
*token*
*secret*
*credential*
*password*
*.env
.env.*

# Specific credential directories
google_drive/Claude/
github/*.odt
credentials/
secrets/

# SSH keys
id_rsa
id_dsa
id_ecdsa
id_ed25519

# Cloud providers
.aws/
.azure/
.gcp/

# Anthropic specific
.anthropic/
anthropic_api_key*
claude_key*

# GitHub tokens
github_token*
gh_token*
```

**Full file:** `/home/dave/skippy/.gitignore`

---

## Credential Storage Best Practices

### Where to Store Credentials

**✅ SAFE Storage Locations:**
1. **Environment variables** (in shell profile, NOT in Git)
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

2. **Secure credential managers:**
   - `pass` (Linux password manager)
   - `gnome-keyring`
   - `1Password` / `Bitwarden`

3. **Protected local files** (NOT in Git repo):
   ```bash
   # Create secure directory
   mkdir -p ~/.secrets
   chmod 700 ~/.secrets

   # Store credentials
   echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.secrets/anthropic
   chmod 600 ~/.secrets/anthropic

   # Source in scripts
   source ~/.secrets/anthropic
   ```

4. **Cloud secret managers** (for production):
   - AWS Secrets Manager
   - Azure Key Vault
   - GCP Secret Manager

**❌ NEVER Store Credentials:**
- In Git repositories (public or private)
- In filenames visible to Git
- In code comments
- In documentation files tracked by Git
- In configuration files tracked by Git
- In screenshots or PDFs in Git
- In `.odt`, `.docx`, or any document files in Git

---

## Development Workflow

### Starting New Work

```bash
# 1. Ensure hooks are installed
ls -la /home/dave/skippy/.git/hooks/pre-commit

# 2. Check .gitignore is current
cat /home/dave/skippy/.gitignore | grep -A 5 "SECURITY"

# 3. Set up environment variables
source ~/.secrets/anthropic  # If you use this method
```

### Before Every Commit

```bash
# 1. Review changes
git status
git diff

# 2. Run manual scan (optional but recommended)
/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh

# 3. Stage files
git add <files>

# 4. Commit (hook runs automatically)
git commit -m "message"
```

### Before Every Push

```bash
# 1. Final review of commits
git log --oneline -5

# 2. Verify no credentials in recent commits
git diff origin/master..HEAD | grep -i "key\|token\|password"

# 3. Push
git push origin master
```

---

## Claude Code Integration

### When Claude Creates Files

Claude MUST follow this protocol:

1. **Before creating any file with credentials:**
   - Store in non-Git directory (e.g., `~/.secrets/`)
   - OR use environment variables
   - OR prompt user to create manually

2. **Before suggesting git commit:**
   - Run security scan first
   - Verify .gitignore covers all sensitive patterns
   - Confirm with user before committing

3. **When user requests git operations:**
   - Check for staged credential files
   - Block and warn if detected
   - Suggest .gitignore additions

### Example Claude Response

**User:** "Create a script that uses my API key"

**Claude Response:**
```
I'll create the script, but I need to handle the API key securely.

Option 1 (Recommended): Environment variable
- I'll create a script that reads from $ANTHROPIC_API_KEY
- You set it once: export ANTHROPIC_API_KEY="your-key"
- Never stored in Git

Option 2: Secure file
- I'll create script to read from ~/.secrets/anthropic
- You create the file manually (I'll show you how)
- Directory excluded from Git via .gitignore

Which would you prefer?
```

---

## Testing & Verification

### Test the Pre-Commit Hook

```bash
# 1. Create test file with fake credential
echo "ANTHROPIC_API_KEY=sk-ant-test123456789" > test_credential.txt

# 2. Try to stage and commit
git add test_credential.txt
git commit -m "test"

# Expected: BLOCKED by pre-commit hook

# 3. Clean up
git reset HEAD test_credential.txt
rm test_credential.txt
```

### Verify .gitignore

```bash
# 1. Create files that should be ignored
touch api_key.txt
touch github_token.odt
touch .env
touch credentials.json

# 2. Check git status
git status

# Expected: None of these files should appear

# 3. Clean up
rm api_key.txt github_token.odt .env credentials.json
```

---

## Maintenance

### Monthly Review

**Checklist:**
- [ ] Review .gitignore for new patterns needed
- [ ] Check if any credentials were accidentally committed
- [ ] Verify pre-commit hook is still active
- [ ] Update security scan patterns if new services added
- [ ] Test hook with fake credentials

### After Adding New Services

When you start using a new service with API keys:

1. **Add service-specific patterns to .gitignore:**
   ```bash
   echo "# Service Name" >> .gitignore
   echo "service_api_key*" >> .gitignore
   echo ".service/" >> .gitignore
   ```

2. **Add patterns to pre-commit scan script**

3. **Document in this protocol**

---

## Success Metrics

### This Protocol is Working When:

✅ **Zero credentials committed since implementation**
- No Anthropic keys
- No GitHub tokens
- No AWS credentials
- No passwords

✅ **Pre-commit hook active and catching issues**
- Hook blocks commits with credentials
- False positive rate < 5%
- All developers aware of override process

✅ **All credentials in secure storage**
- Environment variables
- Password managers
- Secure files outside Git
- Cloud secret managers

✅ **Team following best practices**
- Checking before commits
- Using credential managers
- Reviewing diffs
- Reporting false positives

---

## Related Protocols

**Integrates With:**
- `git_workflow_protocol.md` - Git commit standards
- `error_logging_protocol.md` - Incident documentation
- `backup_strategy_protocol.md` - Repository backups
- `authorization_protocol.md` - Sensitive operations

**References:**
- `.gitignore` - Comprehensive ignore patterns
- `.git/hooks/pre-commit` - Automated scanning
- `scripts/utility/pre_commit_security_scan_v1.0.0.sh` - Scan script

---

## Quick Reference

### Before Every Commit
```bash
git status                    # Review what's staged
git diff --cached            # Check actual changes
# (pre-commit hook runs automatically)
git commit -m "message"      # Commit if hook passes
```

### If Credentials Detected
```bash
git reset HEAD <file>        # Unstage file
echo "<file>" >> .gitignore  # Ignore permanently
git add .gitignore           # Stage .gitignore
git commit -m "message"      # Commit without credentials
```

### Emergency Cleanup
```bash
git filter-repo --invert-paths --path <file> --force
git push origin --force --all
# Then: Revoke credentials immediately!
```

---

## Version History

**v1.0.0 - 2025-10-31**
- Initial protocol creation
- Triggered by Anthropic API key exposure
- Comprehensive .gitignore created
- Pre-commit hook implemented
- Security scan script created
- Emergency response procedures documented

---

**Status:** ✅ ACTIVE AND MANDATORY
**Priority:** CRITICAL
**Enforcement:** Automated pre-commit hook + manual review
**Owner:** All developers with Git access

**This protocol is live and prevents credential exposure to GitHub.**
```
