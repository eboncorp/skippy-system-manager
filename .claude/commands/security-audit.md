# Security Audit Runner

Run comprehensive security checks on code changes before commit or deployment.

## Instructions

When this skill is invoked, perform a thorough security audit:

### 1. Determine Scope
Ask the user:
- Audit current working directory changes? (`git diff`)
- Audit specific file/directory?
- Audit entire repository?
- Focus on specific vulnerability types?

### 2. Create Audit Session
```bash
AUDIT_DIR="/home/dave/skippy/work/security/$(date +%Y%m%d_%H%M%S)_security_audit"
mkdir -p "$AUDIT_DIR"
```

### 3. Check for Exposed Credentials (CRITICAL)
```bash
# Search for common credential patterns
grep -r -n -i "password\s*=" --include="*.php" --include="*.js" --include="*.py" .
grep -r -n -i "api_key\s*=" --include="*.php" --include="*.js" --include="*.py" .
grep -r -n -i "secret\s*=" --include="*.php" --include="*.js" --include="*.py" .
grep -r -n "DB_PASSWORD" --include="*.php" .

# Check for .env files in git
git ls-files | grep -E "\.env$|credentials|secrets"

# Check for SQL dumps (CRITICAL - these contain passwords!)
find . -name "*.sql" -type f
```

### 4. OWASP Top 10 Vulnerability Scan

**SQL Injection:**
```bash
# Look for unsanitized queries
grep -r -n "\$wpdb->query.*\\\$" --include="*.php" .
grep -r -n "mysql_query.*\\\$" --include="*.php" .
# Should use: $wpdb->prepare()
```

**XSS (Cross-Site Scripting):**
```bash
# Unescaped output
grep -r -n "echo \\\$_" --include="*.php" .
grep -r -n "print \\\$_" --include="*.php" .
# Should use: esc_html(), esc_attr(), wp_kses()
```

**CSRF Protection:**
```bash
# Forms without nonce verification
grep -r -n "wp_nonce_field\|check_admin_referer\|wp_verify_nonce" --include="*.php" .
# Ensure all forms have CSRF protection
```

**Command Injection:**
```bash
# Unsanitized shell commands
grep -r -n "exec(\|system(\|passthru(\|shell_exec(" --include="*.php" .
grep -r -n "subprocess\|os.system\|os.popen" --include="*.py" .
```

**Path Traversal:**
```bash
# File operations with user input
grep -r -n "file_get_contents.*\\\$_\|include.*\\\$_\|require.*\\\$_" --include="*.php" .
```

### 5. WordPress-Specific Checks

**Capability Checks:**
```bash
# Admin functions without permission checks
grep -r -n "current_user_can\|is_admin" --include="*.php" .
# Ensure sensitive operations check capabilities
```

**Data Sanitization:**
```bash
# Input sanitization functions
grep -r -n "sanitize_text_field\|sanitize_email\|absint\|intval" --include="*.php" .
# Compare to raw $_POST/$_GET usage
grep -r -n "\\\$_POST\[\|\\\$_GET\[\|\\\$_REQUEST\[" --include="*.php" .
```

**Direct File Access:**
```bash
# Files without ABSPATH check
for f in $(find . -name "*.php" -type f); do
  if ! grep -q "ABSPATH\|WPINC" "$f"; then
    echo "WARNING: $f may allow direct access"
  fi
done
```

### 6. Dependency Vulnerabilities
```bash
# Check for outdated packages
if [ -f "package.json" ]; then
  npm audit 2>/dev/null || echo "Run: npm audit"
fi

if [ -f "composer.json" ]; then
  composer audit 2>/dev/null || echo "Run: composer audit"
fi
```

### 7. Generate Security Report
```bash
cat > "$AUDIT_DIR/SECURITY_REPORT.md" <<EOF
# Security Audit Report
**Date:** $(date)
**Scope:** {repository/directory}
**Auditor:** Claude Code Security Scanner

## Executive Summary
- **Critical Issues:** {count}
- **High Priority:** {count}
- **Medium Priority:** {count}
- **Low Priority:** {count}
- **Overall Risk Score:** {X}/10

## Critical Findings
{List each critical issue with file:line and remediation}

## Recommendations
1. {Priority fixes}
2. {Code patterns to adopt}
3. {Tools to integrate}

## Files Reviewed
{list}
EOF
```

### 8. Risk Scoring
- **9-10:** Critical - Immediate action required (exposed credentials, SQL injection)
- **7-8:** High - Fix before deployment (XSS, CSRF missing)
- **5-6:** Medium - Fix soon (missing input validation)
- **3-4:** Low - Best practice improvements
- **1-2:** Informational - Code quality suggestions

## Common Remediations

**SQL Injection → Use Prepared Statements:**
```php
// Bad
$wpdb->query("SELECT * FROM table WHERE id = $_GET[id]");
// Good
$wpdb->prepare("SELECT * FROM table WHERE id = %d", intval($_GET['id']));
```

**XSS → Escape Output:**
```php
// Bad
echo $_POST['name'];
// Good
echo esc_html($_POST['name']);
```

**CSRF → Add Nonce:**
```php
// In form
wp_nonce_field('my_action', 'my_nonce');
// In handler
check_admin_referer('my_action', 'my_nonce');
```

## Usage
- `/security-audit` - Run full security scan
- Reports saved to `/home/dave/skippy/work/security/`
- Integrates with your 37+ existing security tests
