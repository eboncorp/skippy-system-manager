# Content Migration Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

Converting content between formats (Markdown → HTML, text → WordPress, etc.) requires systematic handling to preserve formatting, verify conversion, and prevent data loss.

## Purpose

- Ensure accurate content conversion
- Preserve formatting and structure
- Verify conversion quality
- Document source and process

---

## Supported Conversions

| From | To | Tool |
|------|----|----|
| Markdown | HTML | Python markdown library |
| Text | WordPress | wp post create/update |
| HTML | WordPress | wp post create/update |

---

## Markdown → HTML Conversion

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_markdown_conversion"
mkdir -p "$SESSION_DIR"

# Copy source
cp /source/document.md "$SESSION_DIR/source.md"

# Convert
python3 <<PYEOF > "$SESSION_DIR/converted.html"
import markdown
with open("$SESSION_DIR/source.md") as f:
    content = f.read()
html = markdown.markdown(content, extensions=['tables', 'fenced_code', 'nl2br'])
print(html)
PYEOF

# Review conversion
cat "$SESSION_DIR/converted.html"

# Apply to WordPress
wp post update {ID} --post_content="$(cat "$SESSION_DIR/converted.html")"

# Verify
wp post get {ID} --field=post_content > "$SESSION_DIR/after.html"
```

---

## Conversion Checklist

- [ ] Source file backed up
- [ ] Conversion completed without errors
- [ ] Output reviewed for quality
- [ ] Tables converted correctly
- [ ] Code blocks preserved
- [ ] Links functional
- [ ] Images handled (if applicable)
- [ ] Applied to WordPress
- [ ] Verified in WordPress

---

## Common Issues

**Tables don't render:**
- Ensure `tables` extension enabled
- Check markdown table syntax

**Line breaks missing:**
- Add `nl2br` extension
- Check paragraph spacing

**Links broken:**
- Verify relative vs absolute paths
- Test all links after conversion

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
