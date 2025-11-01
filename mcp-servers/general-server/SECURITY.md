# Security Documentation - MCP Server v2.0.0

**Last Updated**: 2025-11-01
**Server Version**: 2.0.0

---

## 🔒 Credential Management

### SSH Credentials

**Location**: `/home/dave/skippy/mcp-servers/general-server/.env`

**Format**:
```
EBON_HOST=ebon@10.0.0.29
EBON_PASSWORD=REDACTED_SERVER_PASSWORD
```

**Security Measures**:
- ✅ File permissions: `600` (read/write owner only)
- ✅ Excluded from git: Added to `.gitignore`
- ✅ Not committed to repository
- ⚠️ Currently using password authentication

**Recommended Improvement**: Switch to SSH key authentication
```bash
# Generate SSH key if needed
ssh-keygen -t ed25519 -C "ebonhawk-to-ebon"

# Copy to ebon server
ssh-copy-id ebon@10.0.0.29

# Then remove password from .env and update server.py
```

---

## 🛡️ Tool Security Features

### Database Tools

**Tool**: `mysql_query_safe`

**Security**: Blocks ALL destructive operations
```python
BLOCKED_KEYWORDS = ['DELETE', 'UPDATE', 'DROP', 'ALTER', 'INSERT',
                    'TRUNCATE', 'CREATE', 'REPLACE', 'GRANT', 'REVOKE']
```

**Allowed**: SELECT queries only (read-only)

**Examples**:
- ✅ `SELECT * FROM wp_posts LIMIT 10`
- ❌ `DELETE FROM wp_posts WHERE id=1`
- ❌ `UPDATE wp_options SET option_value='new'`

### WordPress Tools

**Tool**: `wp_search_replace`

**Security**: Defaults to dry-run mode
```python
def wp_search_replace(search: str, replace: str, dry_run: bool = True)
```

**Safety**:
- ⚠️ Default `dry_run=True` - shows what WOULD change without changing it
- ✅ Must explicitly set `dry_run=False` to apply changes
- ✅ Prevents accidental database modifications

**Tool**: `wp_db_export`

**Security**: Creates timestamped backups
- ✅ Never overwrites existing backups
- ✅ Stored in `/home/dave/RunDaveRun/backups/`
- ✅ Timestamped format: `wp_db_backup_YYYYMMDD_HHMMSS.sql`

### Git Operations

**Tool**: `run_credential_scan`

**Security**: Integrated with Pre-Commit Sanitization Protocol
```bash
Script: /home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh
```

**Scans for**:
- API keys
- Passwords
- Tokens
- Private keys
- Credentials in code

**Usage**: Run before EVERY commit
```
Run credential scan before committing
```

---

## 📝 Tools with Write Access

### File System Write Operations

| Tool | Write Access | Risk Level | Safety Measures |
|------|--------------|------------|-----------------|
| `write_file` | YES | HIGH | User must specify path |
| `wordpress_quick_backup` | YES | LOW | Creates backups only |
| `wp_db_export` | YES | LOW | Creates backups only |
| `run_shell_command` | YES | HIGH | User controls command |
| `run_remote_command` | YES | HIGH | SSH to ebon server |

### Read-Only Tools

All other tools (38 of 43) are **read-only**:
- File reading tools
- System monitoring tools
- Database query tool (SELECT only)
- Log analysis tools
- Status check tools
- Search tools

---

## ⚠️ Known Security Considerations

### 1. SSH Password in .env

**Issue**: Password stored in plaintext in .env file

**Current Mitigation**:
- File permissions: 600 (owner read/write only)
- Excluded from git repository
- Local machine only (not exposed externally)

**Recommended Fix**: Switch to SSH key authentication

### 2. Shell Command Execution

**Tools**: `run_shell_command`, `run_remote_command`

**Risk**: Can execute arbitrary shell commands

**Mitigation**:
- All subprocess calls have timeouts (5-120 seconds)
- User must explicitly provide commands
- No command injection from untrusted input
- Commands logged to stderr

### 3. WordPress Path Hardcoded

**Paths in server.py**:
```python
WORDPRESS_PATH = "/home/dave/RunDaveRun"
SKIPPY_PATH = "/home/dave/skippy"
```

**Risk**: If paths change, tools break

**Current Status**: Acceptable for personal use

**Future Enhancement**: Move to .env configuration

### 4. MCP Server Runs with User Permissions

**Permissions**: Runs as user `dave`

**Access**: Full access to all files owned by `dave`

**Mitigation**:
- Only runs on local machine (ebonhawk)
- Accessed only through Claude for Desktop
- No network exposure
- No external API access

---

## 🔐 Protocol Compliance

### Pre-Commit Sanitization Protocol

**Requirement**: Scan all commits for credentials before pushing

**Implementation**: `run_credential_scan` tool

**Usage**:
```
Before committing:
1. "Run credential scan on skippy"
2. Review any findings
3. Remove any credentials found
4. Re-scan to verify clean
5. Then commit
```

**Script**: `/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh`

### Script Creation Protocol

**Requirement**: Check existing 226+ scripts before creating new ones

**Implementation**: `search_skippy_scripts` tool

**Usage**:
```
Before creating a new script:
1. "Search for existing scripts about [topic]"
2. Review results
3. Modify existing script if suitable
4. Only create new if nothing exists
```

---

## 🚨 Emergency Procedures

### If Credentials Are Exposed

1. **Immediately change the password**:
   ```bash
   ssh ebon@10.0.0.29 'passwd'
   ```

2. **Update .env file** with new password:
   ```bash
   nano /home/dave/skippy/mcp-servers/general-server/.env
   ```

3. **If committed to git**, use git-filter-repo to remove from history:
   ```bash
   # DANGER: Rewrites git history
   git filter-repo --path .env --invert-paths
   ```

4. **Restart MCP server** (restart Claude for Desktop)

### If Server Behaves Unexpectedly

1. **Check MCP logs**:
   ```bash
   tail -f ~/.config/Claude/logs/mcp*.log
   ```

2. **Stop the server**:
   - Quit Claude for Desktop completely

3. **Review recent commands** in conversation history

4. **Restart server** with monitoring:
   ```bash
   # Manual test
   /home/dave/skippy/mcp-servers/general-server/.venv/bin/python3 \
     /home/dave/skippy/mcp-servers/general-server/server.py
   ```

---

## ✅ Security Checklist

Before each session:
- [ ] .env file has correct permissions (600)
- [ ] .env is in .gitignore
- [ ] No credentials in server.py code
- [ ] MCP server logs look clean

Before committing code:
- [ ] Run credential scan: `run_credential_scan`
- [ ] Review git diff: `git_diff`
- [ ] Verify no .env file in staged changes
- [ ] Check git status: `git_status`

After WordPress changes:
- [ ] Backup created before changes
- [ ] Search-replace tested with dry-run first
- [ ] Database export successful

---

## 📚 Related Documentation

- **Pre-Commit Sanitization Protocol**: `/home/dave/skippy/conversations/pre_commit_sanitization.md`
- **WordPress Maintenance Protocol**: `/home/dave/skippy/conversations/wordpress_maintenance.md`
- **Script Creation Protocol**: `/home/dave/skippy/conversations/script_creation_protocol.md`
- **Git Workflow Protocol**: `/home/dave/skippy/conversations/git_workflow.md`

---

## 🔄 Security Update History

### v2.0.0 (2025-11-01)
- ✅ Moved SSH credentials to .env file
- ✅ Added .env to .gitignore
- ✅ Created SECURITY.md documentation
- ✅ Set .env file permissions to 600

### v2.0.0 (2025-10-31)
- Added credential scanning integration
- Added database query safety (SELECT-only)
- Added WordPress dry-run defaults
- Added subprocess timeouts

### v1.0.0 (2025-10-31)
- Initial release
- SSH password hardcoded (FIXED in v2.0.0)

---

**Security Contact**: Dave (local system only)
**Last Security Review**: 2025-11-01
**Next Review Recommended**: Monthly
