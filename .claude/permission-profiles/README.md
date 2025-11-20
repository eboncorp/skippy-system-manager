# Permission Profiles

**Version:** 1.0.0
**Created:** 2025-11-19

Context-aware permission profiles for different project types.

---

## Available Profiles

### 1. wordpress-permissive.json

**Use Case:** WordPress content development

**Characteristics:**
- Read operations auto-approved
- Write operations require approval via hooks
- Enforcement hooks active (approval + fact-check)
- Optimized for efficiency
- Session directory requirements enforced

**Use When:**
- Working on WordPress content
- Updating pages/posts/policies
- Campaign website development

**Usage:**
```bash
claude --permissions-profile wordpress-permissive
# Or set in project-specific config
```

---

### 2. script-dev-restrictive.json

**Use Case:** Script development and automation

**Characteristics:**
- Minimal auto-approval (read-only)
- Most operations require explicit approval
- System operations blocked
- Code review integration
- Safety-first approach

**Use When:**
- Developing new scripts
- Modifying automation
- Working on system tools
- Security-sensitive development

**Usage:**
```bash
claude --permissions-profile script-dev-restrictive
# Or set in project-specific config
```

---

## Profile Structure

Each profile includes:

### 1. Auto-Approve Section
Tools and operations that don't require user confirmation:
- Read-only operations
- Safe bash commands
- File pattern whitelists

### 2. Require-Approval Section
Operations that need user approval:
- File modifications
- Write operations
- Execution commands
- Conditions for approval

### 3. Blocked Section
Always-blocked operations:
- Dangerous commands
- System-level operations
- Sensitive file modifications

### 4. Enforcement Hooks
Which hooks are active for this profile:
- WordPress update protection
- Fact-check enforcement
- Sensitive file protection

### 5. Context Loading
Auto-loaded workflows and documentation:
- Session-start workflows
- Context-specific guides

### 6. Requirements
Profile-specific requirements:
- Session directories
- File naming standards
- Testing requirements
- Documentation standards

---

## How Permission Profiles Work

### 1. Profile Selection

**Automatic (Recommended):**
```bash
# Profile selected based on working directory
cd /path/to/wordpress/project
claude
# Automatically uses wordpress-permissive profile
```

**Manual:**
```bash
claude --permissions-profile wordpress-permissive
```

**Project Config:**
```json
{
  "project": "rundaverun-wordpress",
  "default_profile": "wordpress-permissive"
}
```

### 2. Permission Evaluation

When Claude attempts an operation:

1. **Check Auto-Approve List**
   - If tool/command is auto-approved → Execute immediately
   - Example: `Read`, `Grep`, `cat`, `ls`

2. **Check Blocked List**
   - If tool/command is blocked → Deny immediately
   - Example: `rm -rf`, sensitive files

3. **Check Require-Approval List**
   - If in list → Request user approval
   - Apply any conditions
   - Example: `Edit` requires session directory

4. **Run Enforcement Hooks**
   - Execute active hooks for the profile
   - Example: WordPress updates check approval + fact-check

5. **Execute or Deny**
   - Based on cumulative checks

---

## Creating Custom Profiles

### Template

```json
{
  "name": "custom-profile",
  "description": "Custom permissions for specific use case",
  "version": "1.0.0",
  "created": "YYYY-MM-DD",
  "use_case": "Brief description",

  "auto_approve": {
    "tools": ["Read", "Grep", "Glob"],
    "bash_commands": ["cat", "ls", "pwd"],
    "file_patterns": ["*.md", "*.txt"]
  },

  "require_approval": {
    "tools": ["Edit", "Write"],
    "bash_commands": ["git commit *"],
    "conditions": {}
  },

  "blocked": {
    "tools": [],
    "bash_commands": ["rm -rf *", "sudo *"],
    "file_patterns": [".env", "*.key"]
  },

  "enforcement_hooks": {
    "enabled": ["hook1.sh", "hook2.sh"],
    "disabled": []
  },

  "notes": []
}
```

### Validation

```bash
# Validate profile JSON
jq . wordpress-permissive.json

# Test profile
claude --permissions-profile custom-profile --dry-run
```

---

## Best Practices

### 1. Choose Appropriate Profile

- **WordPress work** → wordpress-permissive
- **Script development** → script-dev-restrictive
- **Code review** → script-dev-restrictive
- **Sensitive data** → script-dev-restrictive

### 2. Review Auto-Approve Lists

Periodically review what's auto-approved:
- Ensure read-only operations only
- No destructive commands
- Appropriate for use case

### 3. Keep Blocked Lists Current

Update blocked operations as new risks identified:
- New attack patterns
- Discovered vulnerabilities
- Team incidents

### 4. Document Profile Usage

In project README:
```markdown
## Claude Code Setup
This project uses the `wordpress-permissive` permission profile.

To start working:
\`\`\`bash
claude --permissions-profile wordpress-permissive
\`\`\`
```

### 5. Test Profile Changes

Before deploying profile changes:
```bash
# Test in dry-run mode
claude --permissions-profile new-profile --dry-run

# Monitor first few sessions
# Adjust based on friction points
```

---

## Integration with Hooks

Permission profiles work alongside enforcement hooks:

**WordPress Profile:**
- Enables: WordPress update protection
- Enables: Fact-check enforcement
- Enables: Sensitive file protection
- Auto-loads: WordPress workflow

**Script Dev Profile:**
- Enables: Sensitive file protection only
- Disables: WordPress-specific hooks
- Auto-loads: Script development workflow

---

## Switching Profiles

### Mid-Session

```bash
# Switch to different profile
claude switch-profile script-dev-restrictive
```

### Per-Command

```bash
# Use specific profile for one command
claude --profile wordpress-permissive "update page 105"
```

### Project-Specific

Create `.claude/config.json`:
```json
{
  "default_profile": "wordpress-permissive",
  "profile_detection": "auto"
}
```

---

## Troubleshooting

### Profile Not Loading

**Check:**
1. Profile file exists in `.claude/permission-profiles/`
2. JSON is valid (`jq . profile.json`)
3. Profile name matches file name

### Operations Blocked Unexpectedly

**Check:**
1. Review blocked list in active profile
2. Check enforcement hooks output
3. Verify conditions in require-approval section

### Operations Not Requesting Approval

**Check:**
1. Tool/command is in auto-approve list
2. File pattern matches whitelist
3. Profile is actually active

---

## Security Considerations

**Profile Security:**
- Profiles stored in `.claude/permission-profiles/`
- Read-only for non-owner
- Changes logged to audit trail

**Sensitive Operations:**
- Always blocked regardless of profile
- Multiple layers of protection
- Enforcement hooks run first

**Audit Trail:**
- All profile switches logged
- Permission denials recorded
- Approval requests tracked

---

**Status:** ✅ Active
**Profiles:** 2 (wordpress-permissive, script-dev-restrictive)
**Default:** Auto-detect based on working directory
