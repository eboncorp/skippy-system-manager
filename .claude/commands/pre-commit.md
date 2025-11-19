# Pre-Commit Hook Validator

Enforce naming conventions, prevent /tmp/ usage, and validate code quality before commits.

## Instructions

When this skill is invoked, perform pre-commit validation checks:

### 1. Determine Scope
```bash
# Get staged files
STAGED_FILES=$(git diff --cached --name-only)

# Get modified files (not yet staged)
MODIFIED_FILES=$(git diff --name-only)

# All changes
ALL_CHANGES=$(git status --short)
```

### 2. File Naming Convention Check
```bash
echo "## File Naming Validation"

# Rule: lowercase with underscores, no capitals, no spaces
for file in $STAGED_FILES; do
  BASENAME=$(basename "$file")

  # Check for uppercase letters
  if echo "$BASENAME" | grep -q '[A-Z]'; then
    echo "❌ VIOLATION: $file contains uppercase letters"
    echo "   Should be: $(echo "$BASENAME" | tr '[:upper:]' '[:lower:]' | tr ' -' '__')"
  fi

  # Check for spaces
  if echo "$BASENAME" | grep -q ' '; then
    echo "❌ VIOLATION: $file contains spaces"
    echo "   Should be: $(echo "$BASENAME" | tr ' ' '_')"
  fi

  # Check for hyphens (should be underscores)
  if echo "$BASENAME" | grep -q '-'; then
    echo "⚠️  WARNING: $file uses hyphens (prefer underscores)"
    echo "   Suggested: $(echo "$BASENAME" | tr '-' '_')"
  fi
done

echo "✅ File naming check complete"
```

### 3. Prevent /tmp/ Usage (CRITICAL)
```bash
echo "## Temporary File Location Check"

# Search for /tmp/ in staged files
VIOLATIONS=$(git diff --cached | grep -n "^+.*\/tmp\/" | grep -v "^+++")

if [ -n "$VIOLATIONS" ]; then
  echo "❌ CRITICAL VIOLATION: /tmp/ usage detected!"
  echo "$VIOLATIONS"
  echo ""
  echo "SOLUTION: Use SESSION_DIR instead of /tmp/"
  echo 'SESSION_DIR="/home/dave/skippy/work/{category}/$(date +%Y%m%d_%H%M%S)_description"'
  echo 'mkdir -p "$SESSION_DIR"'
  echo 'Use: "$SESSION_DIR/filename.ext" NOT /tmp/filename.ext'
  BLOCK_COMMIT=true
fi
```

### 4. Security Checks
```bash
echo "## Security Validation"

# Check for exposed credentials
for file in $STAGED_FILES; do
  if [[ "$file" =~ \.(php|js|py|sh)$ ]]; then
    # Hardcoded passwords
    if grep -n "password\s*=\s*['\"]" "$file" 2>/dev/null; then
      echo "❌ SECURITY: Hardcoded password in $file"
      BLOCK_COMMIT=true
    fi

    # API keys
    if grep -n "api_key\s*=\s*['\"]" "$file" 2>/dev/null; then
      echo "❌ SECURITY: Hardcoded API key in $file"
      BLOCK_COMMIT=true
    fi

    # Database credentials
    if grep -n "DB_PASSWORD\|mysql_connect\|mysqli_connect" "$file" 2>/dev/null | grep -v "define.*getenv"; then
      echo "⚠️  WARNING: Database credentials in $file (ensure using environment variables)"
    fi
  fi
done

# Check for .env files
if echo "$STAGED_FILES" | grep -q "\.env$"; then
  echo "❌ CRITICAL: .env file staged for commit!"
  echo "   Add to .gitignore: .env"
  BLOCK_COMMIT=true
fi

# Check for SQL dumps
if echo "$STAGED_FILES" | grep -q "\.sql$"; then
  echo "❌ CRITICAL: SQL dump file staged for commit!"
  echo "   SQL files may contain sensitive data (passwords, emails)"
  echo "   Add to .gitignore: *.sql"
  BLOCK_COMMIT=true
fi
```

### 5. WordPress Code Quality
```bash
echo "## WordPress Code Standards"

for file in $STAGED_FILES; do
  if [[ "$file" =~ \.php$ ]]; then
    # Direct file access protection
    if ! grep -q "ABSPATH\|WPINC\|defined\s*(" "$file"; then
      echo "⚠️  WARNING: $file may allow direct access"
      echo "   Add: if (!defined('ABSPATH')) exit;"
    fi

    # Unsanitized input
    if grep -n '\$_POST\[.*\]' "$file" | grep -v "sanitize_\|intval\|absint"; then
      echo "⚠️  WARNING: $file has unsanitized \$_POST input"
    fi

    # Unescaped output
    if grep -n "echo\s*\\\$_" "$file"; then
      echo "⚠️  WARNING: $file has unescaped output"
      echo "   Use: esc_html(), esc_attr(), wp_kses()"
    fi
  fi
done
```

### 6. Script Versioning Check
```bash
echo "## Script Versioning"

for file in $STAGED_FILES; do
  if [[ "$file" =~ \.sh$ ]]; then
    # Check for version in filename
    if ! echo "$file" | grep -q "_v[0-9]\+\.[0-9]\+\.[0-9]\+\.sh$"; then
      echo "⚠️  WARNING: $file missing semantic version"
      echo "   Pattern: {purpose}_{task}_v{X.Y.Z}.sh"
      echo "   Example: backup_database_v1.0.0.sh"
    fi

    # Check for version in script header
    if ! grep -q "^# Version:" "$file" 2>/dev/null; then
      echo "⚠️  WARNING: $file missing version header comment"
    fi
  fi
done
```

### 7. Documentation Check
```bash
echo "## Documentation Validation"

# If adding new scripts, ensure README update
NEW_SCRIPTS=$(echo "$STAGED_FILES" | grep "\.sh$")
README_UPDATED=$(echo "$STAGED_FILES" | grep -i "readme\|documentation")

if [ -n "$NEW_SCRIPTS" ] && [ -z "$README_UPDATED" ]; then
  echo "⚠️  WARNING: New scripts added but no documentation updated"
  echo "   Consider updating relevant README files"
fi

# Check for TODO comments
TODOS=$(git diff --cached | grep "^+.*TODO\|FIXME\|HACK" | head -5)
if [ -n "$TODOS" ]; then
  echo "ℹ️  INFO: TODO/FIXME comments added:"
  echo "$TODOS"
fi
```

### 8. Generate Pre-Commit Report
```bash
PRECOMMIT_DIR="/home/dave/skippy/work/precommit/$(date +%Y%m%d_%H%M%S)_validation"
mkdir -p "$PRECOMMIT_DIR"

cat > "$PRECOMMIT_DIR/VALIDATION_REPORT.md" <<EOF
# Pre-Commit Validation Report
**Date:** $(date)
**Files Staged:** $(echo "$STAGED_FILES" | wc -w)
**Branch:** $(git branch --show-current)

## Summary
- **Blocking Issues:** {count}
- **Warnings:** {count}
- **Info:** {count}

## Violations Found
{List each issue}

## Recommendation
- **SAFE TO COMMIT:** No blocking issues
- **BLOCK COMMIT:** Fix critical issues first
- **PROCEED WITH CAUTION:** Review warnings
EOF
```

### 9. Auto-Fix Common Issues
```bash
# Offer to fix simple issues automatically
echo "## Auto-Fix Options"

# Fix file naming
for file in $STAGED_FILES; do
  NEW_NAME=$(echo "$file" | tr '[:upper:]' '[:lower:]' | tr ' -' '__')
  if [ "$file" != "$NEW_NAME" ]; then
    echo "Fix: git mv '$file' '$NEW_NAME'"
  fi
done

# Remove /tmp/ references
echo "Fix: sed -i 's|/tmp/|\"$SESSION_DIR/\"|g' <file>"
```

### 10. Install as Git Hook
```bash
# Create actual git pre-commit hook
cat > .git/hooks/pre-commit <<'HOOK'
#!/bin/bash
# Auto-generated pre-commit hook

# Check for /tmp/ usage
if git diff --cached | grep -q "^+.*\/tmp\/"; then
  echo "ERROR: /tmp/ usage detected! Use SESSION_DIR instead."
  exit 1
fi

# Check for uppercase filenames
for file in $(git diff --cached --name-only); do
  if echo "$(basename "$file")" | grep -q '[A-Z]'; then
    echo "ERROR: Uppercase in filename: $file"
    exit 1
  fi
done

# Check for .env files
if git diff --cached --name-only | grep -q "\.env$"; then
  echo "ERROR: .env file staged for commit!"
  exit 1
fi

exit 0
HOOK

chmod +x .git/hooks/pre-commit
echo "Git pre-commit hook installed"
```

## Usage
- `/pre-commit` - Run validation on staged changes
- Can install as actual git hook for automatic enforcement
- Reports saved to `/home/dave/skippy/work/precommit/`
- Enforces your established conventions automatically

## Enforcement Levels
- **BLOCK (❌):** Critical issues that must be fixed
- **WARNING (⚠️):** Should fix but not blocking
- **INFO (ℹ️):** Suggestions for improvement
