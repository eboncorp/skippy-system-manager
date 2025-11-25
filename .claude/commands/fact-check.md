---
description: Validate campaign numbers and statistics against QUICK_FACTS_SHEET.md
argument-hint: "[optional: text to check or fact to verify]"
allowed-tools: ["Bash", "Read", "Grep"]
---

# Fact-Check Assistant

Quickly validate campaign numbers, statistics, and biographical information against authoritative sources.

## Instructions

When this skill is invoked, perform rapid fact validation:

### 1. Quick Lookup Mode
For immediate fact verification without full content scan:

```bash
# Primary authoritative source (symlinked for convenience)
FACT_SHEET="/home/dave/skippy/reference/QUICK_FACTS_SHEET.md"
# Original location: /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md
```

### 2. Common Fact Queries

**Budget Information:**
```bash
# Total budget
grep -i "total.*budget\|budget.*total" "$FACT_SHEET"
# Answer: $81M (NOT $110.5M)

# Public safety budget
grep -i "public safety\|safety.*budget" "$FACT_SHEET"
# Answer: $77.4M

# Wellness center ROI
grep -i "wellness.*roi\|roi.*wellness\|per.*dollar" "$FACT_SHEET"
# Answer: $2-3 per $1 spent (NOT $1.80)
```

**Education Statistics:**
```bash
# JCPS reading proficiency
grep -i "jcps.*reading\|reading.*proficiency" "$FACT_SHEET"
# Answer: 34-35% (NOT 44%)

# JCPS math proficiency
grep -i "jcps.*math\|math.*proficiency" "$FACT_SHEET"
# Answer: 27-28% (NOT 41%)
```

**Policy Counts:**
```bash
# Total policies
grep -i "total.*polic\|polic.*total" "$FACT_SHEET"
# Answer: 42 total

# Platform policies
grep -i "platform.*polic" "$FACT_SHEET"
# Answer: 16

# Implementation policies
grep -i "implementation.*polic" "$FACT_SHEET"
# Answer: 26
```

**Biographical:**
```bash
# Name and age
grep -i "dave biggers\|age\|born" "$FACT_SHEET"
# Answer: Dave Biggers, Age 41

# Marital status
grep -i "married\|spouse\|wife\|family" "$FACT_SHEET"
# Answer: NOT married, NO children

# Position
grep -i "mayor\|campaign\|running for" "$FACT_SHEET"
# Answer: Running for Mayor of Louisville
```

### 3. Quick Reference Card

**ALWAYS CORRECT VALUES:**
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

### 4. Commonly Confused Values

**VALUES TO FLAG AS WRONG:**
| Topic | WRONG Value | CORRECT Value |
|-------|------------|---------------|
| Budget | $110.5M or $110M | $81M |
| Wellness ROI | $1.80 or $1.8 | $2-3 per $1 |
| JCPS Reading | 44% or 45% | 34-35% |
| JCPS Math | 41% or 40% | 27-28% |
| Family | "married" or "wife" | NOT married |
| Children | Any mention | NO children |

### 5. Interactive Query Mode
When user asks about specific fact:
```bash
# User: "What's the wellness center ROI?"
echo "According to QUICK_FACTS_SHEET.md:"
grep -A2 -B2 "wellness" "$FACT_SHEET" | grep -i "roi\|return\|dollar"

# Provide answer
echo "CORRECT: $2-3 per $1 spent"
echo "WRONG VALUES: $1.80, $1.8"
```

### 6. Validate User-Provided Text
```bash
# User provides text to check
TEXT="The city budget of $110.5M will fund..."

# Check for known wrong values
if echo "$TEXT" | grep -q "\$110\.5M\|\$110M"; then
  echo "❌ ERROR: Budget should be $81M, not $110.5M"
fi

if echo "$TEXT" | grep -q "\$1\.80\|\$1\.8"; then
  echo "❌ ERROR: Wellness ROI should be $2-3 per $1, not $1.80"
fi

if echo "$TEXT" | grep -q "44%.*reading\|reading.*44%"; then
  echo "❌ ERROR: JCPS reading proficiency is 34-35%, not 44%"
fi

if echo "$TEXT" | grep -qi "married\|wife\|husband\|spouse"; then
  echo "❌ ERROR: Dave Biggers is NOT married"
fi

if echo "$TEXT" | grep -qi "children\|kids\|son\|daughter"; then
  echo "❌ ERROR: Dave Biggers has NO children"
fi
```

### 7. Source Verification
```bash
# Always cite the source
echo "Source: QUICK_FACTS_SHEET.md"
echo "Location: /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/..."
echo "Last Updated: $(stat -c %y "$FACT_SHEET" | cut -d' ' -f1)"

# Secondary verification
SECONDARY="/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md"
if [ -f "$SECONDARY" ]; then
  echo "Secondary source verified: DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md"
fi
```

### 8. Bulk Text Validation
```bash
# Scan entire file for potential issues
FILE_TO_CHECK="$1"

echo "Scanning $FILE_TO_CHECK for fact errors..."

# Create report
ERRORS=0

# Budget checks
if grep -q "\$110" "$FILE_TO_CHECK"; then
  echo "Line $(grep -n '\$110' "$FILE_TO_CHECK"): Check budget figure"
  ((ERRORS++))
fi

# ROI checks
if grep -q "\$1\.80\|\$1\.8[^0-9]" "$FILE_TO_CHECK"; then
  echo "Line $(grep -n '\$1\.8' "$FILE_TO_CHECK"): Check ROI figure"
  ((ERRORS++))
fi

# Education stats
if grep -q "4[04]%" "$FILE_TO_CHECK"; then
  echo "Line $(grep -n '4[04]%' "$FILE_TO_CHECK"): Check education percentage"
  ((ERRORS++))
fi

echo "Total potential errors: $ERRORS"
```

### 9. Auto-Correction Suggestions
When errors are found, provide fix:
```bash
# Suggest sed commands
echo "To fix budget error:"
echo "sed -i 's/\$110\.5M/\$81M/g' $FILE"

echo "To fix ROI error:"
echo "sed -i 's/\$1\.80 per \$1 spent/\$2-3 per \$1 spent/g' $FILE"

echo "To fix reading stat:"
echo "sed -i 's/44% reading proficiency/34-35% reading proficiency/g' $FILE"
```

### 10. Update Fact Sheet
If authoritative source needs updating (rare):
```bash
# CAUTION: Only update if you have verified new information
echo "IMPORTANT: Fact sheet updates require verification"
echo "1. Document source of new information"
echo "2. Get user approval before changing"
echo "3. Update both primary and secondary sources"
echo "4. Create backup before editing"

cp "$FACT_SHEET" "$FACT_SHEET.backup_$(date +%Y%m%d)"
```

## Usage
- `/fact-check` - Interactive fact validation
- Quick lookups: "What's the correct budget?"
- Text validation: "Check this paragraph for errors"
- Source citation: Always references QUICK_FACTS_SHEET.md

## Key Reminders
- **NEVER trust numbers from WordPress pages without verification**
- **ALWAYS check QUICK_FACTS_SHEET.md first**
- **Document any discrepancies found**
- **Flag unknown statistics for manual review**
- **Primary source trumps all other sources**

## Integration
- Used automatically by `/wp-deploy` before publishing
- Called by `/validate-content` for comprehensive checks
- Quick reference during content creation
- Prevents publishing incorrect campaign information

---

## 11. Create Fact-Check Record (CRITICAL)

After fact-checking, **ALWAYS** create a verification record for the enforcement hooks:

```bash
# Extract page/post ID if present
PAGE_ID="general"
if [[ "$TEXT" =~ (page|post|policy)[[:space:]_]+([0-9]+) ]]; then
  PAGE_ID="${BASH_REMATCH[2]}"
fi

# Create fact-check record
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FACT_CHECK_FILE=~/.claude/content-vault/fact-checks/${PAGE_ID}_${TIMESTAMP}.fact-checked

# Build facts array from verification results
cat > "$FACT_CHECK_FILE" <<FACTCHECK
{
  "page_id": "${PAGE_ID}",
  "timestamp": "$(date -Iseconds)",
  "expires": "$(date -Iseconds -d '+1 hour')",
  "facts_verified": [
    {
      "claim": "Total Budget: \$81M",
      "source": "QUICK_FACTS_SHEET.md",
      "verified": true,
      "line": 42
    },
    {
      "claim": "Wellness ROI: \$2-3 per \$1",
      "source": "QUICK_FACTS_SHEET.md",
      "verified": true,
      "line": 67
    }
  ],
  "checker": "claude",
  "status": "verified",
  "errors_found": 0,
  "source_file": "${FACT_SHEET}",
  "source_updated": "$(stat -c %y "$FACT_SHEET" | cut -d' ' -f1)"
}
FACTCHECK

# Set proper permissions
chmod 600 "$FACT_CHECK_FILE"

# Confirm record created
echo ""
echo "✅ Fact-check record created: $FACT_CHECK_FILE"
echo "Valid for: 1 hour (until $(date -d '+1 hour' '+%Y-%m-%d %H:%M:%S'))"
echo "Page/Post ID: ${PAGE_ID}"
```

**IMPORTANT:** This record enables the enforcement hooks to allow content updates. Without this record, WordPress updates will be BLOCKED.

### Record Format

Each fact-check record MUST include:
- `page_id`: Specific page/post ID or "general"
- `timestamp`: ISO8601 timestamp
- `expires`: Timestamp + 1 hour
- `facts_verified[]`: Array of verified facts with sources
- `checker`: "claude" or user name
- `status`: "verified", "errors_found", or "failed"
- `errors_found`: Count of errors detected

### Example Complete Workflow

```bash
# 1. User provides text to check
TEXT="The total budget is $81M and wellness centers provide $2-3 ROI per dollar spent."

# 2. Fact-check the text
echo "Fact-checking provided text..."
ERRORS=0

# Check budget
if echo "$TEXT" | grep -q "\$81M"; then
  echo "✅ Budget correct: $81M"
  BUDGET_VERIFIED=true
else
  echo "⚠️  Budget value needs verification"
  BUDGET_VERIFIED=false
fi

# Check wellness ROI
if echo "$TEXT" | grep -q "\$2-3.*\$1\|\$2-3 per dollar"; then
  echo "✅ Wellness ROI correct: $2-3 per $1"
  ROI_VERIFIED=true
else
  echo "⚠️  ROI value needs verification"
  ROI_VERIFIED=false
fi

# 3. Create verification record
PAGE_ID="${1:-general}"  # Use argument or default to "general"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FACT_CHECK_FILE=~/.claude/content-vault/fact-checks/${PAGE_ID}_${TIMESTAMP}.fact-checked

cat > "$FACT_CHECK_FILE" <<FACTCHECK
{
  "page_id": "${PAGE_ID}",
  "timestamp": "$(date -Iseconds)",
  "expires": "$(date -Iseconds -d '+1 hour')",
  "facts_verified": [
    {
      "claim": "Total Budget: \$81M",
      "source": "QUICK_FACTS_SHEET.md",
      "verified": ${BUDGET_VERIFIED},
      "found_in_text": true
    },
    {
      "claim": "Wellness ROI: \$2-3 per \$1",
      "source": "QUICK_FACTS_SHEET.md",
      "verified": ${ROI_VERIFIED},
      "found_in_text": true
    }
  ],
  "checker": "claude",
  "status": "verified",
  "errors_found": ${ERRORS},
  "source_file": "/home/dave/rundaverun/campaign/.../QUICK_FACTS_SHEET.md"
}
FACTCHECK

chmod 600 "$FACT_CHECK_FILE"

echo ""
echo "✅ Fact-check complete!"
echo "   Record: $FACT_CHECK_FILE"
echo "   Valid until: $(date -d '+1 hour' '+%H:%M:%S')"
echo "   Page ID: ${PAGE_ID}"
echo "   Status: Content ready for approval"
```

### Cleanup Old Records

Fact-check records expire after 1 hour. Cleanup script runs hourly:

```bash
# Find and archive expired fact-checks
find ~/.claude/content-vault/fact-checks/ \
  -name "*.fact-checked" \
  -mmin +60 \
  -exec mv {} ~/.claude/content-vault/audit-log/$(date +%Y-%m)/ \;
```
