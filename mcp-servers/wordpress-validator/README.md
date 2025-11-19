# WordPress Content Validator MCP Server

**Version:** 1.0.0
**Created:** 2025-11-19
**Type:** MCP Server

Multi-level content validation for WordPress pages and posts.

---

## Features

### Validation Types

1. **Facts Validation**
   - Checks against QUICK_FACTS_SHEET.md
   - Detects incorrect budget figures
   - Verifies statistical data
   - Flags biographical errors

2. **Link Validation**
   - Detects localhost links
   - Finds broken internal links
   - Identifies empty/placeholder links
   - Validates link structure

3. **SEO Validation**
   - Meta tags presence
   - Title/H1 heading structure
   - Image alt text
   - Heading hierarchy

4. **Accessibility Validation (WCAG 2.1)**
   - Alt text on images
   - ARIA labels
   - Proper heading hierarchy
   - Color contrast (future)

5. **HTML Validation**
   - Unclosed tags
   - Malformed markup
   - Tag nesting issues

---

## Validation Levels

### Standard
- Facts validation
- Link checking
**Use for:** Draft content

### Strict
- All Standard checks
- SEO validation
**Use for:** Pre-review content

### Publish-Ready
- All Strict checks
- Accessibility validation
- HTML validation
**Use for:** Final pre-publish check

---

## Installation

### 1. Add to Claude Code MCP Config

Edit `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "wordpress-validator": {
      "command": "python3",
      "args": ["/home/dave/skippy-system-manager/mcp-servers/wordpress-validator/server.py"],
      "type": "stdio"
    }
  }
}
```

### 2. Restart Claude Code

```bash
# Restart Claude Code to load MCP server
```

---

## Usage

### Via MCP Tool Call

```python
# Standard validation
result = mcp_tool("wordpress-validator", "validate_content", {
    "content": "<html>...</html>",
    "level": "standard"
})

# Publish-ready validation
result = mcp_tool("wordpress-validator", "validate_content", {
    "content": page_content,
    "level": "publish-ready"
})
```

### Response Format

```json
{
  "timestamp": "2025-11-19T10:30:00Z",
  "validation_level": "publish-ready",
  "overall_status": "fail",
  "facts": {
    "status": "fail",
    "errors": [
      {
        "type": "incorrect_fact",
        "field": "budget",
        "found": "$110.5M",
        "correct": "$81M",
        "severity": "critical"
      }
    ],
    "warnings": [],
    "facts_checked": ["budget", "wellness_roi", "jcps_reading", ...]
  },
  "links": {
    "status": "pass",
    "errors": [],
    "warnings": [...],
    "links_found": 42
  },
  "seo": {...},
  "accessibility": {...},
  "html": {...}
}
```

---

## Integration

### With /validate-content Command

```bash
# Validate page before publishing
/validate-content --page-id=105 --level=publish-ready
```

### With WordPress Workflow

```bash
# In session directory
cat "$SESSION_DIR/page_105_final.html" | \
  python3 mcp-servers/wordpress-validator/server.py validate

# Check result
if [ $? -eq 0 ]; then
  echo "✅ Validation passed"
else
  echo "❌ Validation failed - review errors"
fi
```

### With Enforcement Hooks

The validation can be integrated into pre-publish hooks to block updates that fail validation.

---

## Error Severity Levels

**Critical:**
- Incorrect facts (budget, statistics)
- Biographical errors
- Major HTML errors

**High:**
- Missing accessibility features
- Broken links
- Unclosed HTML tags

**Medium:**
- SEO issues
- Missing meta tags
- Heading hierarchy

**Low:**
- Empty placeholder links
- Minor formatting issues

---

## Fact Sheet Integration

Automatically loads facts from:
1. Primary: `/home/dave/rundaverun/campaign/.../QUICK_FACTS_SHEET.md`
2. Secondary: `/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md`

---

## Example Workflow

```bash
# 1. Create content
cat > page_105_final.html <<EOF
<h1>Dave Biggers for Mayor</h1>
<p>Total budget: \$81M</p>
<p>Wellness centers provide \$2-3 ROI per dollar</p>
EOF

# 2. Validate (standard)
python3 server.py <<JSON
{
  "method": "validate_content",
  "params": {
    "content": "$(cat page_105_final.html)",
    "level": "standard"
  }
}
JSON

# 3. If passes, validate (publish-ready)
python3 server.py <<JSON
{
  "method": "validate_content",
  "params": {
    "content": "$(cat page_105_final.html)",
    "level": "publish-ready"
  }
}
JSON

# 4. If all pass, proceed with approval
```

---

**Status:** ✅ Active
**Dependencies:** Python 3.7+, QUICK_FACTS_SHEET.md
**MCP Protocol:** stdio
