# Content Migration Workflow

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

Standard workflow for migrating content between environments (local ↔ staging ↔ production) or converting formats (Markdown → HTML → WordPress).

---

## Migration Types

| From | To | Use Case |
|------|----|----- ----|
| Local WP | Production WP | Deploy tested changes |
| Production WP | Local WP | Sync for development |
| Markdown | WordPress | Convert documentation |
| HTML files | WordPress | Import legacy content |

---

## Local → Production Migration

### Step 1: Create Session Directory
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_migration"
mkdir -p "$SESSION_DIR"
```

### Step 2: Export Local Content
```bash
# Single page
wp post get {ID} --field=post_content > "$SESSION_DIR/page_{ID}_local.html"

# Multiple pages
for id in 105 110 115; do
  wp post get $id --field=post_content > "$SESSION_DIR/page_${id}_local.html"
done
```

### Step 3: Validate Content
```bash
# Check for campaign facts
grep -E '\$[0-9]+|[0-9]+%' "$SESSION_DIR/page_{ID}_local.html"

# Cross-reference with QUICK_FACTS_SHEET.md
```

### Step 4: Transfer to Production
```bash
# Copy file to production server
SSH_AUTH_SOCK="" scp -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  "$SESSION_DIR/page_{ID}_local.html" \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com:/tmp/

# Apply update
SSH_AUTH_SOCK="" ssh ... \
  'cd html && wp post update {ID} --post_content="$(cat /tmp/page_{ID}_local.html)" --allow-root'
```

### Step 5: Flush Caches & Verify
```bash
SSH_AUTH_SOCK="" ssh ... 'cd html && wp cache flush --allow-root'
curl -s https://rundaverun.org/page-slug/ | grep "expected text"
```

---

## Production → Local Migration

### Step 1: Export from Production
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_sync"
mkdir -p "$SESSION_DIR"

SSH_AUTH_SOCK="" ssh ... \
  'cd html && wp post get {ID} --field=post_content' > "$SESSION_DIR/page_{ID}_prod.html"
```

### Step 2: Import to Local
```bash
wp post update {ID} --post_content="$(cat "$SESSION_DIR/page_{ID}_prod.html")" --allow-root
```

### Step 3: Verify
```bash
wp post get {ID} --field=post_content > "$SESSION_DIR/page_{ID}_local_after.html"
diff "$SESSION_DIR/page_{ID}_prod.html" "$SESSION_DIR/page_{ID}_local_after.html"
```

---

## Markdown → WordPress Migration

### Step 1: Prepare Source
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_md_import"
mkdir -p "$SESSION_DIR"
cp /source/document.md "$SESSION_DIR/source.md"
```

### Step 2: Convert to HTML
```python
python3 << 'EOF'
import markdown

with open('source.md', 'r') as f:
    content = f.read()

# Convert with extensions
html = markdown.markdown(content, extensions=[
    'tables',
    'fenced_code',
    'nl2br',
    'toc'
])

with open('converted.html', 'w') as f:
    f.write(html)
EOF
```

### Step 3: Review & Clean
```bash
# Check output
cat "$SESSION_DIR/converted.html"

# Fix any issues manually if needed
```

### Step 4: Import to WordPress
```bash
# Create new page
wp post create --post_type=page \
  --post_title="Page Title" \
  --post_content="$(cat "$SESSION_DIR/converted.html")" \
  --post_status=draft \
  --allow-root

# Or update existing
wp post update {ID} --post_content="$(cat "$SESSION_DIR/converted.html")" --allow-root
```

---

## Bulk Migration

### Export All Pages
```bash
# Get list of page IDs
wp post list --post_type=page --format=ids --allow-root > page_ids.txt

# Export each
for id in $(cat page_ids.txt); do
  wp post get $id --field=post_content > "$SESSION_DIR/page_${id}.html"
  wp post get $id --field=post_title > "$SESSION_DIR/page_${id}_title.txt"
done
```

### Import All Pages
```bash
for id in $(cat page_ids.txt); do
  wp post update $id --post_content="$(cat $SESSION_DIR/page_${id}.html)" --allow-root
done
```

---

## URL Migration

When migrating between domains:

```bash
# Dry run first
wp search-replace 'http://old-domain.com' 'https://new-domain.com' --dry-run --allow-root

# Execute
wp search-replace 'http://old-domain.com' 'https://new-domain.com' --allow-root

# Flush
wp cache flush --allow-root
wp rewrite flush --allow-root
```

---

## Verification Checklist

- [ ] Source content backed up
- [ ] Fact-checking completed
- [ ] URLs updated if needed
- [ ] Images accessible
- [ ] Links functional
- [ ] Formatting preserved
- [ ] diff comparison shows expected changes

---

## Related

- WordPress Update Workflow
- Backup Workflow
- Deployment Workflow
