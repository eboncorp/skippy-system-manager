# Campaign Content Validator

Cross-reference campaign content against authoritative fact sources to ensure accuracy.

## Instructions

When this skill is invoked, validate campaign content for factual accuracy:

### 1. Identify Content Source
Ask the user:
- Validate specific file/URL?
- Validate WordPress page/post by ID?
- Validate text pasted directly?
- Validate all policy documents?

### 2. Load Authoritative Sources
```bash
# PRIMARY SOURCE - Always check this first
FACT_SHEET="/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md"

# Secondary source
CAMPAIGN_FACTS="/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md"

# Verify sources exist
if [ ! -f "$FACT_SHEET" ]; then
  echo "ERROR: Primary fact sheet not found!"
  exit 1
fi
```

### 3. Extract Numbers & Statistics
From the content being validated, identify:
- Dollar amounts ($XXM, $X.XX billion)
- Percentages (XX%)
- Counts (42 policies, 16 platform documents)
- ROI figures ($X per $1)
- Budget allocations
- Test scores/proficiency rates

### 4. Cross-Reference Against Known Values

**CRITICAL BUDGET FIGURES:**
| Item | CORRECT Value | WRONG Values to Flag |
|------|--------------|---------------------|
| Total Budget | $1.2 billion | $81M, $110.5M, $110M |
| Public Safety | $77.4M | Other values |
| Wellness ROI | $5.60 per $1 | $2-3, $1.80, $1.8 |
| Mini Substations | 63 total | 46 |
| JCPS Reading | 34-35% | 44%, 45% |
| JCPS Math | 27-28% | 41%, 40% |
| Policy Documents | 42 total | Other counts |
| Platform Policies | 16 | Other counts |
| Implementation Policies | 26 | Other counts |

**BIOGRAPHICAL FACTS:**
| Item | CORRECT Value | WRONG Values to Flag |
|------|--------------|---------------------|
| Full Name | Dave Biggers | Other names |
| Age | 41 | Other ages |
| Marital Status | NOT married | "married", "wife" |
| Children | NO children | Any mention of kids |
| City | Louisville | Other cities |
| Position Sought | Mayor | Other offices |

### 5. Generate Validation Report
```bash
VALIDATION_DIR="/home/dave/skippy/work/validation/$(date +%Y%m%d_%H%M%S)_content_validation"
mkdir -p "$VALIDATION_DIR"

cat > "$VALIDATION_DIR/VALIDATION_REPORT.md" <<EOF
# Content Validation Report
**Date:** $(date)
**Content Source:** {file/page/text}
**Validator:** Claude Code Fact Checker

## Summary
- **Total Facts Checked:** {count}
- **Verified Correct:** {count}
- **ERRORS FOUND:** {count}
- **Warnings:** {count}

## ERRORS (Must Fix)
{List each error with:}
- Found: "$110.5M budget"
- Correct: "$81M budget"
- Location: Line X or Section Y
- Source: QUICK_FACTS_SHEET.md

## Warnings (Review)
{Ambiguous or potentially outdated info}

## Verified Facts
{List of correct facts found}

## Recommendation
{SAFE TO PUBLISH / NEEDS CORRECTIONS}
EOF
```

### 6. Automated Correction Suggestions
For each error found, provide:
```bash
# sed command to fix
sed -i 's/\$81M/\$1.2 billion/g' "$FILE"
sed -i 's/\$110\.5M/\$1.2 billion/g' "$FILE"
sed -i 's/\$2-3 per \$1/\$5.60 per \$1/g' "$FILE"
sed -i 's/\$1\.80 per \$1/\$5.60 per \$1/g' "$FILE"
sed -i 's/44% reading/34-35% reading/g' "$FILE"
```

### 7. WordPress Content Validation
If validating WordPress content:
```bash
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"

# Get content from WordPress
wp --path="$WP_PATH" post get {ID} --field=post_content > "$VALIDATION_DIR/content_to_validate.html"

# Extract text (remove HTML)
sed 's/<[^>]*>//g' "$VALIDATION_DIR/content_to_validate.html" > "$VALIDATION_DIR/content_text.txt"

# Search for numbers
grep -E '\$[0-9]+\.?[0-9]*[MBK]|\d+%|\d+\s+(policies|documents)' "$VALIDATION_DIR/content_text.txt"
```

### 8. Batch Validation
For validating all policy documents:
```bash
# Get all policy post IDs
POLICY_IDS=$(wp --path="$WP_PATH" post list --post_type=policy --field=ID)

for ID in $POLICY_IDS; do
  echo "Validating policy $ID..."
  wp --path="$WP_PATH" post get $ID --field=post_content > "$VALIDATION_DIR/policy_${ID}.html"
  # Run fact checks on each
done
```

## Usage Examples
- `/validate-content` - Interactive validation session
- Validates numbers, percentages, biographical info
- Cross-references QUICK_FACTS_SHEET.md
- Generates correction commands
- Prevents publishing incorrect information

## Important Notes
- NEVER trust numbers from existing WordPress pages without verification
- ALWAYS check QUICK_FACTS_SHEET.md first
- Document any updates to authoritative sources
- Flag any numbers not found in authoritative sources for manual review
