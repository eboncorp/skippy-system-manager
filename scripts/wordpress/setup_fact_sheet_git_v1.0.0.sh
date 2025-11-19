#!/bin/bash
# Setup Fact Sheet Version Control
# Version: 1.0.0
# Purpose: Initialize git tracking for QUICK_FACTS_SHEET.md with automated validation
# Usage: bash setup_fact_sheet_git_v1.0.0.sh

VERSION="1.0.0"
FACT_SHEET_DIR="/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files"
FACT_SHEET="$FACT_SHEET_DIR/QUICK_FACTS_SHEET.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Fact Sheet Version Control Setup v$VERSION ===${NC}"
echo ""

# Check if fact sheet exists
if [ ! -f "$FACT_SHEET" ]; then
    echo -e "${RED}❌ Fact sheet not found!${NC}"
    echo "Expected: $FACT_SHEET"
    exit 1
fi

echo -e "${GREEN}✅ Found fact sheet${NC}"
echo "Location: $FACT_SHEET"
echo ""

# Navigate to directory
cd "$FACT_SHEET_DIR" || exit 1

# Check if already a git repo
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git repository already exists${NC}"
    echo ""
    git log --oneline QUICK_FACTS_SHEET.md | head -5
    echo ""
    read -p "Reinitialize? This will preserve history. (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Keeping existing git repository."
        exit 0
    fi
else
    echo "Initializing git repository..."
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
    echo ""
fi

# Create .gitignore
cat > .gitignore <<'EOF'
# Ignore everything except QUICK_FACTS_SHEET.md and validation scripts
*
!.gitignore
!QUICK_FACTS_SHEET.md
!fact_sheet_validator.sh
!README.md
EOF

echo -e "${GREEN}✅ Created .gitignore${NC}"

# Create validator script
cat > fact_sheet_validator.sh <<'EOF'
#!/bin/bash
# Fact Sheet Validator
# Validates QUICK_FACTS_SHEET.md before commits

FACT_SHEET="QUICK_FACTS_SHEET.md"

# Check 1: File exists
if [ ! -f "$FACT_SHEET" ]; then
    echo "❌ QUICK_FACTS_SHEET.md not found!"
    exit 1
fi

# Check 2: Has required sections
required_sections=(
    "# Quick Facts"
    "## Budget Overview"
    "## Education Statistics"
    "## Public Safety"
)

for section in "${required_sections[@]}"; do
    if ! grep -q "^$section" "$FACT_SHEET"; then
        echo "❌ Missing required section: $section"
        exit 1
    fi
done

# Check 3: Has dollar amounts
if ! grep -qE '\$[0-9]+(\.[0-9]+)?M' "$FACT_SHEET"; then
    echo "❌ No budget figures found (expected format: \$XX.XM)"
    exit 1
fi

# Check 4: Has percentages
if ! grep -qE '[0-9]{1,3}%' "$FACT_SHEET"; then
    echo "❌ No percentage statistics found"
    exit 1
fi

# Check 5: No obviously wrong values
wrong_values=(
    '\$110.5M'
    '\$1.80'
    '44%.*reading'
    '41%.*math'
)

for value in "${wrong_values[@]}"; do
    if grep -qE "$value" "$FACT_SHEET"; then
        echo "❌ Found outdated/incorrect value: $value"
        exit 1
    fi
done

echo "✅ Fact sheet validation passed"
exit 0
EOF

chmod +x fact_sheet_validator.sh
echo -e "${GREEN}✅ Created fact sheet validator${NC}"

# Create pre-commit hook
mkdir -p .git/hooks
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Pre-commit hook for QUICK_FACTS_SHEET.md validation

if git diff --cached --name-only | grep -q "QUICK_FACTS_SHEET.md"; then
    echo "Validating QUICK_FACTS_SHEET.md..."

    # Run validator
    if ! ./fact_sheet_validator.sh; then
        echo ""
        echo "❌ Fact sheet validation failed!"
        echo "Fix the issues above before committing."
        exit 1
    fi

    echo "✅ Fact sheet validation passed"
fi

exit 0
EOF

chmod +x .git/hooks/pre-commit
echo -e "${GREEN}✅ Created pre-commit hook${NC}"

# Create README
cat > README.md <<'EOF'
# QUICK_FACTS_SHEET Version Control

This directory is under version control to track changes to the fact sheet.

## How to Update

1. Edit QUICK_FACTS_SHEET.md
2. Run validator: `./fact_sheet_validator.sh`
3. Stage changes: `git add QUICK_FACTS_SHEET.md`
4. Commit: `git commit -m "Update: description of changes"`
5. View history: `git log QUICK_FACTS_SHEET.md`

## Validator

The validator checks for:
- Required sections present
- Budget figures in correct format
- Percentage statistics present
- No outdated/incorrect values

Validation runs automatically before commits.

## Viewing Changes

```bash
# See what changed
git diff QUICK_FACTS_SHEET.md

# See history
git log --oneline QUICK_FACTS_SHEET.md

# View specific version
git show <commit>:QUICK_FACTS_SHEET.md

# Compare versions
git diff <old-commit> <new-commit> QUICK_FACTS_SHEET.md

# Revert to previous version
git checkout <commit> QUICK_FACTS_SHEET.md
```

## Integration with WordPress

When fact sheet is updated:
1. Commit changes here
2. Run fact checker: `/home/dave/skippy/development/scripts/scripts/monitoring/automated_fact_checker_v1.0.0.sh`
3. Fix any violations found in WordPress content
4. Document updates in session notes

---

**Setup:** $(date)
**Version:** 1.0.0
EOF

echo -e "${GREEN}✅ Created README.md${NC}"
echo ""

# Initial commit if not already committed
if ! git log --oneline | grep -q .; then
    echo "Creating initial commit..."

    git add .gitignore QUICK_FACTS_SHEET.md fact_sheet_validator.sh README.md

    git commit -m "Initial commit: Add QUICK_FACTS_SHEET.md version control

Setup version control for fact sheet with:
- Automated validation before commits
- Pre-commit hook to prevent invalid data
- Validator script to check fact sheet integrity
- README with usage instructions

This ensures fact sheet changes are tracked and validated.

🤖 Generated with Claude Code
Tool: setup_fact_sheet_git_v1.0.0.sh v$VERSION"

    echo -e "${GREEN}✅ Initial commit created${NC}"
else
    echo -e "${YELLOW}ℹ️  Existing commits found, skipping initial commit${NC}"
fi

echo ""
echo -e "${BLUE}=== Setup Complete ===${NC}"
echo ""
echo "Fact sheet is now under version control!"
echo ""
echo "Directory: $FACT_SHEET_DIR"
echo ""
echo "Next steps:"
echo "  1. Make changes to QUICK_FACTS_SHEET.md"
echo "  2. Test validator: cd $FACT_SHEET_DIR && ./fact_sheet_validator.sh"
echo "  3. Commit changes: git add QUICK_FACTS_SHEET.md && git commit -m 'Update: description'"
echo ""
echo "Commands:"
echo "  git log QUICK_FACTS_SHEET.md          # View change history"
echo "  git diff QUICK_FACTS_SHEET.md         # See uncommitted changes"
echo "  ./fact_sheet_validator.sh             # Run validation manually"
echo ""
