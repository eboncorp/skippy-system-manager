# Authorization Protocol

**Date Created**: 2025-10-28
**Purpose**: When and how to use Claude authorization for sensitive operations
**Script Location**: `/home/dave/scripts/system/authorize_claude`
**Grant Window**: 4 hours
**Priority**: CRITICAL (security-sensitive)

## Overview

The authorization system grants Claude temporary permission to perform sensitive operations that could affect system stability or data integrity. This protocol defines when authorization is required and how to properly use it.

## When Authorization is Required

### ALWAYS Require Authorization

**Mass Operations** (10+ items):
- ✅ Renaming 10+ files or directories
- ✅ Deleting multiple files
- ✅ Moving files between directories (bulk)
- ✅ Permission changes affecting multiple files
- ✅ Search-and-replace operations across multiple files

**System Changes**:
- ✅ Modifying system configuration files
- ✅ Installing/removing system packages
- ✅ Changing system services
- ✅ Network configuration changes
- ✅ User/group modifications

**Production Operations**:
- ✅ Production database modifications
- ✅ Production file deployments
- ✅ Production server configuration changes
- ✅ Domain/DNS changes

**Data Operations**:
- ✅ Database drops/resets
- ✅ Large data imports/exports
- ✅ Data migrations
- ✅ Backup restorations

### May Require Authorization

**Development Operations** (use judgment):
- Local database resets (backup exists → OK without auth)
- Local file operations (reversible → OK without auth)
- Git operations on local branches (OK without auth)
- WordPress local testing (OK without auth)

## Authorization Command

### Running Authorization

**Method 1: Direct Script** (Works immediately):
```bash
bash /home/dave/scripts/system/authorize_claude
```

**Method 2: Slash Command** (Requires Claude restart):
```bash
/authorize_claude
```

**Note**: The slash command (`/authorize_claude`) will not work until Claude Code is restarted after the command file was created. Always use the direct script method if unsure.

### Authorization Output

Successful authorization shows:
```
Authorization granted for 4 hours
Expires: 2025-10-28 XX:XX:XX
```

### Checking Authorization Status

The script automatically checks if authorization is still valid:
- **Within 4-hour window**: Operations proceed
- **Expired**: Must re-authorize
- **Never granted**: Must authorize before proceeding

## Authorization Workflow

### Standard Authorization Flow

1. **User Request**: User asks for operation requiring authorization
2. **Claude Identifies**: Claude recognizes sensitive operation
3. **Ask User**: "This operation requires authorization. Run: `/authorize_claude` or `bash /home/dave/scripts/system/authorize_claude`"
4. **User Runs**: User executes authorization command
5. **Proceed**: Claude performs authorized operation
6. **Document**: Claude notes authorization window in operation log

### Example Conversation

```
User: "Rename all 300 files to lowercase"

Claude: "This operation requires authorization (300 files affected).
Please run: bash /home/dave/scripts/system/authorize_claude

Then let me know when you've authorized."

User: "authorized"

Claude: [Checks authorization timestamp]
Authorization confirmed. Expires: 2025-10-28 04:37:07
Proceeding with file renaming operation...
[Performs operation]
```

## What Authorization Grants

### Permitted Operations (During 4-hour window)

**File Operations**:
- Bulk file renaming
- Mass file deletion
- Bulk permission changes
- Large file moves

**Database Operations**:
- Database drops/resets
- Large imports/exports
- Schema modifications
- Data migrations

**System Operations**:
- Configuration changes
- Service restarts
- Package installations
- User/group changes

**Production Operations**:
- Production deployments
- Production database changes
- Server configuration
- DNS/domain changes

## What Authorization Does NOT Grant

Authorization does **NOT** override safety rules:

**Still Prohibited**:
- ❌ Deleting files without backup
- ❌ Force pushing to main branch
- ❌ Skipping git hooks
- ❌ Committing without user request
- ❌ Bypassing deployment checklist
- ❌ Skipping testing procedures

Authorization grants **permission** to perform sensitive operations,
but **safety protocols still apply**.

## Authorization Best Practices

### Before Requesting Authorization

**Claude Should**:
1. Identify the operation as sensitive
2. Explain why authorization is needed
3. Estimate impact (e.g., "300 files affected")
4. Suggest backup if appropriate
5. Ask user to authorize

**Example**:
```
This operation requires authorization because:
- Affects 300+ files
- Irreversible without backup
- System-wide impact

Suggested steps:
1. Create backup (Y/N)?
2. Run authorization: bash /home/dave/scripts/system/authorize_claude
3. Proceed with operation
```

### During Authorized Window

**Claude Should**:
1. Verify authorization timestamp
2. Check expiration time
3. Note time remaining if close to expiration
4. Perform operation systematically
5. Document what was done

### After Authorization Expires

**Claude Should**:
1. Note authorization has expired
2. Ask for re-authorization if more work needed
3. Do NOT perform sensitive operations without re-auth

## Authorization Documentation

### Logging Authorized Operations

When performing authorized operations, document:

```markdown
Authorization Used:
- Granted: 2025-10-28 12:37:07
- Expires: 2025-10-28 16:37:07
- Operation: Mass file renaming (300 files)
- Backup: Created at /home/dave/reorganization_backup/
- Result: Success - all files renamed
- Issues: None
```

### Track Authorization Usage

Keep record of:
- What operations were authorized
- When authorization was used
- What was accomplished
- Any issues encountered
- Backup locations

## Authorization + Backup Integration

### Always Combine Authorization with Backup

**Before authorized operation**:
```bash
# 1. User authorizes
bash /home/dave/scripts/system/authorize_claude

# 2. Claude creates backup
mkdir -p /home/dave/backups/pre_operation_$(date +%Y%m%d_%H%M%S)
# Backup relevant files/directories

# 3. Claude proceeds with operation
# Perform authorized changes

# 4. Claude verifies success
# Check operation completed correctly
```

**Reference**: See `/home/dave/skippy/conversations/backup_strategy_protocol.md`

## Emergency Operations

### When Authorization Can Be Expedited

**Critical Security Issues**:
- Active security breach
- Data loss in progress
- System completely down
- Legal/compliance emergency

**Emergency Protocol**:
1. User grants authorization
2. Claude performs minimal fix
3. Full backup created after stabilization
4. Proper testing done later
5. Incident documented

**Still Required**: Authorization must be granted, even in emergency

## Common Authorization Scenarios

### Scenario 1: Directory Reorganization

**Operation**: Rename 60+ directories, 300+ files
**Authorization**: REQUIRED
**Backup**: REQUIRED
**Procedure**:
1. Create backup (directory structure, file list)
2. Get authorization
3. Perform renames systematically
4. Verify no broken links
5. Document changes

### Scenario 2: WordPress Deployment

**Operation**: Deploy to production
**Authorization**: REQUIRED (production changes)
**Backup**: REQUIRED (database + files)
**Procedure**:
1. Backup production
2. Get authorization
3. Follow deployment checklist
4. Verify deployment
5. Monitor for issues

### Scenario 3: Database Migration

**Operation**: Import large database, modify schema
**Authorization**: REQUIRED
**Backup**: REQUIRED
**Procedure**:
1. Backup current database
2. Get authorization
3. Perform migration
4. Verify data integrity
5. Test application

### Scenario 4: Script Creation

**Operation**: Create new script in skippy/scripts/
**Authorization**: NOT REQUIRED
**Backup**: NOT REQUIRED
**Procedure**:
1. Create script with versioning
2. Set permissions
3. Document in index

## Troubleshooting

### Authorization Script Not Found

```bash
# Check script location
ls -la /home/dave/scripts/system/authorize_claude

# If missing, it should be at:
/home/dave/scripts/system/authorize_claude

# Or original location:
/home/dave/rundaverun/campaign/authorize_claude_v2.sh
```

### Slash Command Not Working

**Issue**: `/authorize_claude` returns "Unknown slash command"
**Cause**: Command file created but Claude not restarted
**Solution**: Use direct script instead:
```bash
bash /home/dave/scripts/system/authorize_claude
```

### Authorization Expired Mid-Operation

**Issue**: Operation started within window, expired during execution
**Solution**:
1. Pause operation if possible
2. Get new authorization
3. Resume operation
4. Document expiration issue

### Uncertain if Authorization Needed

**Guideline**: If you're asking "Do I need authorization?"
**Answer**: Probably yes.

**When in doubt**:
1. Ask user: "This operation affects X items. Authorization recommended?"
2. Err on side of caution
3. Better to ask unnecessarily than break something

## Integration with Other Protocols

### With Backup Protocol
Reference: `/home/dave/skippy/conversations/backup_strategy_protocol.md`
- Always backup before authorized operations
- Document backup location
- Verify backup integrity

### With Git Protocol
Reference: `/home/dave/skippy/conversations/git_workflow_protocol.md`
- Authorization doesn't override git safety rules
- Still requires user request for commits
- Document authorized changes in commit message

### With Deployment Checklist
Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`
- Authorization required for production deployments
- Follow full deployment checklist
- Document authorization in deployment log

### With Error Logging
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Log any issues during authorized operations
- Document what authorization was for
- Track authorization usage patterns

## Quick Reference

### Authorization Needed?

**YES - Require Authorization**:
- Mass operations (10+ files)
- Production changes
- Database modifications
- System configuration
- Irreversible operations

**NO - Authorization Optional**:
- Single file operations
- Local testing
- Reading/viewing operations
- Script creation
- Documentation updates

### Authorization Commands

```bash
# Grant authorization (4 hours)
bash /home/dave/scripts/system/authorize_claude

# Check if script exists
ls -la /home/dave/scripts/system/authorize_claude

# View authorization details
# (Authorization script shows expiration time)
```

### Authorization Checklist

Before requesting authorization from user:
- [ ] Operation is sensitive/risky
- [ ] Affects 10+ items OR production OR database
- [ ] Backup plan exists
- [ ] Impact clearly communicated
- [ ] Alternative safer approach considered

After receiving authorization:
- [ ] Verify authorization timestamp
- [ ] Check expiration time
- [ ] Create backup if needed
- [ ] Perform operation systematically
- [ ] Verify success
- [ ] Document what was done

---

**This protocol is part of the persistent memory system.**
**Reference before requesting user authorization.**
