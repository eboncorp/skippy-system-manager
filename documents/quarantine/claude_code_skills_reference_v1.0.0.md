# Claude Code Skills Reference Guide
**Version:** 1.0.0
**Created:** November 17, 2025
**Author:** Claude Code
**Location:** `/home/dave/skippy/.claude/commands/`

---

## Overview

This document catalogs 8 custom Claude Code skills designed for the Dave Biggers campaign and Skippy development workflows. These skills automate common tasks, enforce standards, and prevent errors.

---

## Skills Summary

| Command | Purpose | Use Case |
|---------|---------|----------|
| `/wp-deploy` | WordPress deployment automation | Content updates with safety checks |
| `/security-audit` | Security vulnerability scanning | Pre-commit/pre-deploy security review |
| `/validate-content` | Campaign fact verification | Ensure accurate statistics |
| `/mcp-health` | MCP server monitoring | Check integration status |
| `/git-branches` | Git branch management | Track branches and conflicts |
| `/pre-commit` | Pre-commit validation | Enforce naming conventions |
| `/session-summary` | Session documentation | Auto-generate README.md |
| `/fact-check` | Quick fact validation | Verify campaign numbers |

---

## Skill Details

### 1. WordPress Deployment Automation (`/wp-deploy`)

**File:** `/home/dave/skippy/.claude/commands/wp-deploy.md`
**Size:** 3.0 KB

**Purpose:**
Automate WordPress content deployment with built-in safety checks, session management, and verification.

**Key Features:**
- Automatic SESSION_DIR creation (no /tmp/ usage)
- Pre-deployment path verification
- Content backup before changes
- Fact validation against QUICK_FACTS_SHEET.md
- Diff verification after updates
- Automatic README.md generation
- Rollback instructions included

**Workflow:**
1. Create session directory with timestamp
2. Verify WordPress path and connectivity
3. Save original state (_before files)
4. Validate content against authoritative sources
5. Save iterations (_v1, _v2, etc.)
6. Apply changes to WordPress
7. Verify with diff (_after files)
8. Document in README.md

**Example Usage:**
```bash
/wp-deploy
# Claude will ask:
# - Which site? (local or production)
# - Description for session
# - Page/Post IDs to update
```

**Critical Reminders:**
- Never use /tmp/ for any files
- Always run diff to verify updates
- Cross-reference numbers with QUICK_FACTS_SHEET.md

---

### 2. Security Audit Runner (`/security-audit`)

**File:** `/home/dave/skippy/.claude/commands/security-audit.md`
**Size:** 4.6 KB

**Purpose:**
Comprehensive security scanning based on OWASP Top 10 vulnerabilities.

**Key Features:**
- Credential exposure detection
- SQL injection scanning
- XSS vulnerability identification
- CSRF protection verification
- Command injection checks
- WordPress-specific security patterns
- Risk scoring (1-10 scale)

**Scans For:**
- Hardcoded passwords/API keys
- .env files in git
- SQL dump files (contain sensitive data)
- Unsanitized database queries
- Unescaped output
- Missing nonce verification
- Direct file access vulnerabilities

**Risk Score Guide:**
- **9-10:** Critical - Immediate action (exposed credentials)
- **7-8:** High - Fix before deploy (XSS, CSRF)
- **5-6:** Medium - Fix soon (missing validation)
- **3-4:** Low - Best practice improvements
- **1-2:** Informational - Code quality suggestions

**Output:**
- Detailed security report in `/home/dave/skippy/work/security/`
- Specific file:line references
- Remediation code examples

**WordPress-Specific Checks:**
```php
// SQL Injection - Bad
$wpdb->query("SELECT * FROM table WHERE id = $_GET[id]");
// SQL Injection - Good
$wpdb->prepare("SELECT * FROM table WHERE id = %d", intval($_GET['id']));

// XSS - Bad
echo $_POST['name'];
// XSS - Good
echo esc_html($_POST['name']);
```

---

### 3. Campaign Content Validator (`/validate-content`)

**File:** `/home/dave/skippy/.claude/commands/validate-content.md`
**Size:** 4.5 KB

**Purpose:**
Cross-reference campaign content against authoritative fact sources to ensure accuracy.

**Authoritative Source:**
```
/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md
```

**Critical Values to Verify:**

| Category | Correct Value | Wrong Values to Flag |
|----------|--------------|---------------------|
| Total Budget | $81M | $110.5M, $110M |
| Public Safety Budget | $77.4M | - |
| Wellness ROI | $2-3 per $1 | $1.80, $1.8 |
| JCPS Reading | 34-35% | 44%, 45% |
| JCPS Math | 27-28% | 41%, 40% |
| Total Policies | 42 | - |
| Platform Policies | 16 | - |
| Implementation Policies | 26 | - |
| Dave's Age | 41 | - |
| Marital Status | NOT married | "married", "wife" |
| Children | NONE | Any mention |

**Output:**
- Validation report with errors/warnings
- Specific sed commands for corrections
- Source citations

**Example Correction:**
```bash
sed -i 's/\$110\.5M/\$81M/g' file.html
sed -i 's/\$1\.80 per \$1 spent/\$2-3 per \$1 spent/g' file.html
```

---

### 4. MCP Server Health Check (`/mcp-health`)

**File:** `/home/dave/skippy/.claude/commands/mcp-health.md`
**Size:** 5.9 KB

**Purpose:**
Monitor and test all 75 MCP server tools across 5 integrations.

**Current Integrations:**

| Integration | Tools | Status |
|-------------|-------|--------|
| Pexels Stock Photos | 4 | ✅ Operational |
| Google Drive | 13 | ✅ Operational |
| Google Photos | 6 | ⚠️ OAuth 403 pending |
| GitHub | 3 | ✅ Operational |
| Slack | 2 | ✅ Operational |

**Checks Performed:**
- Server file existence
- Python environment verification
- API key validation
- OAuth token status and expiration
- Dependency package availability
- Tool endpoint testing

**Health Report Includes:**
- Per-integration status (Operational/Failed/Degraded)
- Tools available vs total
- OAuth token validity
- Overall health percentage
- Recommendations for fixes

**Key Locations:**
```bash
MCP_SERVER_PATH="/home/dave/skippy/mcp-servers/general-server"
GOOGLE_CREDS="~/.config/claude-code/google_credentials.json"
GOOGLE_TOKEN="~/.config/claude-code/google_token.json"
```

---

### 5. Git Branch Manager (`/git-branches`)

**File:** `/home/dave/skippy/.claude/commands/git-branches.md`
**Size:** 6.5 KB

**Purpose:**
Comprehensive git branch analysis, conflict detection, and cleanup recommendations.

**Key Features:**
- Branch status overview (ahead/behind main)
- Merge conflict detection BEFORE merging
- Stale branch identification (>30 days)
- Unmerged commit tracking
- Visual branch graph
- Cleanup recommendations
- Feature branch tracking by pattern

**Analyses:**
- Last commit per branch
- Commits ahead/behind main
- Remote tracking status
- Orphaned remote branches
- Fully merged branches (safe to delete)

**Conflict Detection:**
```bash
# Dry run merge to detect conflicts
git merge-tree $(git merge-base feature master) master feature
```

**Branch Patterns Tracked:**
- `feature/*` - New functionality
- `claude/*` - AI-generated features
- `fix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

**Output:**
- Comprehensive branch report in `/home/dave/skippy/work/git/`
- Visual branch graph
- Recommended cleanup commands
- Safe delete list

---

### 6. Pre-Commit Hook Validator (`/pre-commit`)

**File:** `/home/dave/skippy/.claude/commands/pre-commit.md`
**Size:** 7.2 KB

**Purpose:**
Enforce naming conventions, prevent /tmp/ usage, and validate code quality before commits.

**Enforces:**

1. **File Naming (CRITICAL)**
   - Lowercase with underscores only
   - No capitals, no spaces, no hyphens
   - ❌ `Budget-Update.sh` → ✅ `budget_update.sh`

2. **No /tmp/ Usage (CRITICAL)**
   - Blocks commits with /tmp/ references
   - Must use SESSION_DIR instead

3. **Security Checks**
   - No hardcoded passwords
   - No API keys in code
   - No .env files committed
   - No SQL dump files

4. **WordPress Standards**
   - ABSPATH protection
   - Input sanitization
   - Output escaping

5. **Script Versioning**
   - Semantic version in filename: `script_v1.0.0.sh`
   - Version header comment required

**Violation Levels:**
- **❌ BLOCK:** Critical issues that must be fixed
- **⚠️ WARNING:** Should fix but not blocking
- **ℹ️ INFO:** Suggestions for improvement

**Auto-Fix Commands:**
```bash
# Fix naming
git mv 'Bad-Name.sh' 'bad_name.sh'

# Fix /tmp/ usage
sed -i 's|/tmp/|"$SESSION_DIR/"|g' script.sh
```

**Install as Git Hook:**
```bash
# Creates .git/hooks/pre-commit that auto-runs these checks
chmod +x .git/hooks/pre-commit
```

---

### 7. Session Summary Generator (`/session-summary`)

**File:** `/home/dave/skippy/.claude/commands/session-summary.md`
**Size:** 6.8 KB

**Purpose:**
Automatically create comprehensive README.md documentation for work sessions.

**Analyzes:**
- Session directory contents
- File naming patterns (_before, _v1, _final, _after)
- Timestamp and description from directory name
- Session type (WordPress, Security, Scripts, Git)
- Verification results (diff comparison)

**Generated README.md Includes:**
- Session metadata (date, type, directory)
- Resources modified (IDs extracted from filenames)
- Changes made (summary)
- Complete file listing by category
- Verification results with diff output
- Rollback instructions
- Session statistics (file count, size)

**File Categories:**
- **Before:** Original state backups
- **Iterations:** Edit versions (v1, v2, v3...)
- **Final:** Version applied to system
- **After:** Actual state for verification

**Session Index:**
- Maintains `/home/dave/skippy/work/SESSION_LOG.md`
- Chronological log of all work sessions
- Quick reference for past work

**Integration:**
- Run after `/wp-deploy` to document deployment
- Run after `/security-audit` to document findings
- Run at end of every work session

---

### 8. Fact-Check Assistant (`/fact-check`)

**File:** `/home/dave/skippy/.claude/commands/fact-check.md`
**Size:** 6.4 KB

**Purpose:**
Rapid validation of campaign statistics and biographical information.

**Quick Reference Card:**
```
BUDGET:
- Total Budget: $81M
- Public Safety Budget: $77.4M
- Campaign Budget: $1.2B
- Wellness Center ROI: $2-3 per $1 spent

EDUCATION:
- JCPS Reading Proficiency: 34-35%
- JCPS Math Proficiency: 27-28%

POLICIES:
- Total Policy Documents: 42
- Platform Policies: 16
- Implementation Policies: 26

BIOGRAPHICAL:
- Full Name: Dave Biggers
- Age: 41
- Marital Status: NOT married
- Children: NONE
- City: Louisville, KY
- Office Sought: Mayor
```

**Use Cases:**
- "What's the correct budget?" → $81M
- "Check this paragraph for errors" → Scans for wrong values
- "Validate JCPS stats" → 34-35% reading, 27-28% math

**Source:**
- Primary: QUICK_FACTS_SHEET.md (campaign plugin)
- Secondary: DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md

**Key Principle:**
**NEVER trust numbers from WordPress pages without verification against QUICK_FACTS_SHEET.md**

---

## Integration Between Skills

These skills are designed to work together:

1. **Content Update Workflow:**
   - `/fact-check` → Validate numbers first
   - `/wp-deploy` → Safe deployment with backups
   - `/session-summary` → Document the session

2. **Pre-Release Workflow:**
   - `/security-audit` → Check for vulnerabilities
   - `/pre-commit` → Enforce standards
   - `/validate-content` → Verify all facts
   - `/git-branches` → Ensure clean merge

3. **Monitoring Workflow:**
   - `/mcp-health` → Check tool availability
   - `/git-branches` → Track branch status

---

## Best Practices

1. **Always verify WordPress path** before any WP-CLI operations
2. **Never use /tmp/** - always use SESSION_DIR
3. **Save _before, _vN, _final, _after** for every change
4. **Run diff** to verify updates succeeded
5. **Check QUICK_FACTS_SHEET.md** before publishing any numbers
6. **Document everything** in session README.md
7. **Keep branches short-lived** and prune stale ones
8. **Run security audit** before any production deployment

---

## File Locations

| Item | Path |
|------|------|
| Skills | `/home/dave/skippy/.claude/commands/` |
| Work Sessions | `/home/dave/skippy/work/{category}/{timestamp}/` |
| Fact Sheet | `/home/dave/rundaverun/campaign/.../QUICK_FACTS_SHEET.md` |
| Session Log | `/home/dave/skippy/work/SESSION_LOG.md` |
| Security Reports | `/home/dave/skippy/work/security/` |
| Git Reports | `/home/dave/skippy/work/git/` |
| MCP Health | `/home/dave/skippy/work/mcp/` |

---

## Maintenance

- **Update frequency:** As workflows evolve
- **Version control:** Tracked in git with skippy repo
- **Documentation:** This reference guide
- **Testing:** Manual invocation and validation

---

*Generated by Claude Code*
*November 17, 2025*
