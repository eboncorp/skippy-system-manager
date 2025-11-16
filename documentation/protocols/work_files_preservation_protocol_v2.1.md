# Work Files Preservation Protocol v2.1

**Version:** 2.1
**Last Updated:** November 12, 2025
**Status:** Active
**Supersedes:** v2.0 (November 8, 2025)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | Nov 12, 2025 | Added Step 0 (installation verification), enhanced verification with HTTP/functional testing, binary file handling, theme/plugin procedures, database modification procedures |
| 2.0 | Nov 8, 2025 | WordPress-enhanced with 7-step process |
| 1.0 | Oct 2025 | Initial protocol |

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Standard Workflow: Steps 0-7](#standard-workflow-steps-0-7)
3. [Special Case: Binary/Media Files](#special-case-binarymedia-files)
4. [Special Case: Theme/Plugin Modifications](#special-case-themeplugin-modifications)
5. [Special Case: Database Modifications](#special-case-database-modifications)
6. [Verification Requirements](#verification-requirements)
7. [File Naming Standards](#file-naming-standards)
8. [Cleanup & Archival](#cleanup--archival)

---

## Core Principles

### Why This Protocol Exists

**Problem:** `/tmp/` directory is cleared on system reboot, causing permanent data loss.

**Solution:** All intermediate files must be stored in persistent session directories within `/home/dave/skippy/work/`.

### When This Protocol Applies

**MANDATORY for:**
- ✅ Every WordPress post/page edit
- ✅ Every file modification
- ✅ Every script development session
- ✅ Every diagnostic/debug session
- ✅ ANY command that creates intermediate files
- ✅ Python conversions, sed/awk operations, ANY temp files
- ✅ Media uploads
- ✅ Theme/plugin modifications
- ✅ Database changes

**NO EXCEPTIONS.**

---

## Standard Workflow: Steps 0-7

### Step 0: Verify Installation Path (WordPress Work Only)

**ALWAYS verify correct WordPress installation path BEFORE starting any WordPress work.**

This step prevents the critical error of working on the wrong installation, which can cause:
- Images uploaded to wrong location (404 errors)
- Changes made to inactive site
- Database operations on wrong database

```bash
# 1. Check WordPress database connection
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" db check

# 2. Verify site URL matches expectation
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" option get siteurl
# Expected: http://rundaverun-local-complete-022655.local

# 3. For Local by Flywheel, verify active installation path
cat ~/.config/Local/sites.json | python3 -m json.tool | grep -A 5 "rundaverun"
# Look for "path" field - this is the ACTUAL installation location

# 4. Test HTTP accessibility (if site is running)
curl -I "http://rundaverun-local-complete-022655.local" | grep "HTTP/1.1 200"
```

**If verification fails:**
- Check Local by Flywheel app is running and site is started
- Verify correct site path in Local config
- Check wp-config.php database socket path matches running MySQL
- Verify nginx/Apache is serving the correct document root

**Document verified path in session README.**

---

### Step 1: Create Session Directory FIRST

**BEFORE any work begins, create a timestamped session directory.**

```bash
# WordPress work (production site)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# WordPress work (local development)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Script development
SESSION_DIR="/home/dave/skippy/work/scripts/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Theme/plugin modifications
SESSION_DIR="/home/dave/skippy/work/wordpress/theme_mods/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Database modifications
SESSION_DIR="/home/dave/skippy/work/wordpress/db_mods/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
```

**Description naming conventions:**
- Use underscores: `homepage_fixes` not `homepage-fixes`
- Be specific: `page_105_wellness_roi_update` not `updates`
- 2-5 words maximum
- Lowercase only

**Examples:**
- `20251112_043015_homepage_hero_image_fix`
- `20251112_043530_policy_699_budget_update`
- `20251112_044000_astra_child_featured_images`

---

### Step 2: Save Original State BEFORE Any Changes

**Capture the current state before making ANY modifications.**

```bash
# WordPress pages
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# WordPress posts
wp post get 941 --field=post_content > "$SESSION_DIR/post_941_before.html"

# Policy documents
wp post get 699 --field=post_content > "$SESSION_DIR/policy_699_before.html"

# Theme/plugin files
cp /path/to/functions.php "$SESSION_DIR/functions_before.php"
cp /path/to/plugin.php "$SESSION_DIR/plugin_before.php"

# Configuration files
cp /path/to/wp-config.php "$SESSION_DIR/wp-config_before.php"

# Any other file
cp /path/to/file "$SESSION_DIR/filename_before.ext"
```

**For theme/plugin directories, backup entire directory:**
```bash
cp -r /path/to/wp-content/themes/astra-child "$SESSION_DIR/astra_child_backup/"
```

---

### Step 3: Save Each Iteration

**Every edit creates a versioned file. Never overwrite previous versions.**

```bash
# First edit
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/g' > "$SESSION_DIR/page_105_v1.html"

# Second edit
cat "$SESSION_DIR/page_105_v1.html" | sed 's/foo/bar/g' > "$SESSION_DIR/page_105_v2.html"

# Third edit
cat "$SESSION_DIR/page_105_v2.html" | sed 's/baz/qux/g' > "$SESSION_DIR/page_105_v3.html"

# Python conversion (MUST use SESSION_DIR, NOT /tmp/)
python3 << PYEOF > "$SESSION_DIR/page_331_converted.html"
import markdown
with open("$SESSION_DIR/source.md") as f:
    print(markdown.markdown(f.read()))
PYEOF

# ANY intermediate file
echo "temp data" > "$SESSION_DIR/temp_data.txt"  # NOT /tmp/temp_data.txt
```

**Key principle:** Every intermediate state gets its own file.

---

### Step 4: Save Final Version BEFORE Applying

**Create a `_final` version that will be applied to the live system.**

```bash
# This is the version you're about to apply
cp "$SESSION_DIR/page_105_v3.html" "$SESSION_DIR/page_105_final.html"
```

**Why separate final version?**
- Clear marker of "this is what was applied"
- Easy rollback reference
- Audit trail

---

### Step 5: Apply Changes to Actual System

**Now apply the final version to the live system.**

```bash
# WordPress content update
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# File update
cp "$SESSION_DIR/script_final.sh" /actual/location/script.sh

# Database update
wp db query < "$SESSION_DIR/query_final.sql"

# Theme file update
cp "$SESSION_DIR/functions_final.php" /path/to/wp-content/themes/astra-child/functions.php
```

---

### Step 6: VERIFY - Multi-Level Verification

**THIS STEP IS CRITICAL - DO NOT SKIP**

The verification step has three components:

#### A. Database Verification (WordPress Content)

```bash
# Get actual content from system after update
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"

# Compare to verify update worked
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# If diff shows differences, INVESTIGATE before proceeding
```

**What this catches:**
- Failed updates
- Content modified by WordPress hooks/filters
- Encoding issues
- Incomplete writes

#### B. HTTP Verification (Public Resources)

**For media uploads, public files, or any web-accessible resource:**

```bash
# Get site URL
SITE_URL=$(wp --path="/home/dave/skippy/rundaverun_local_site/app/public" option get siteurl)

# Test uploaded image is accessible
curl -I "$SITE_URL/wp-content/uploads/2025/11/image.jpg" | grep "HTTP" >> "$SESSION_DIR/http_verification.log"

# Expected: HTTP/1.1 200 OK
# NOT: HTTP/1.1 404 Not Found

# Test multiple resources
cat > "$SESSION_DIR/test_urls.txt" <<EOF
$SITE_URL/wp-content/uploads/2025/11/image1.jpg
$SITE_URL/wp-content/uploads/2025/11/image2.jpg
$SITE_URL/wp-content/themes/astra-child/style.css
EOF

while read url; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    echo "$url: $HTTP_CODE" >> "$SESSION_DIR/http_verification.log"
done < "$SESSION_DIR/test_urls.txt"

# Review results
cat "$SESSION_DIR/http_verification.log"
```

**What this catches:**
- Files uploaded to wrong location
- Incorrect file permissions
- Web server configuration issues
- Path mismatches between filesystem and HTTP

#### C. Functional Verification (Actual Behavior)

**Test that changes work as intended:**

```bash
# Test page renders correctly
curl -s "$SITE_URL/?p=105" | grep "expected content string" && \
    echo "✅ Page renders correctly" || \
    echo "⚠️  Page render check failed"

# Test featured image appears in HTML
curl -s "$SITE_URL/?p=105" | grep -o 'og:image.*content="[^"]*"' | head -1

# Test form submission (if applicable)
curl -X POST -d "field=value" "$SITE_URL/submit" | grep "success"

# Test JavaScript functionality (if applicable)
curl -s "$SITE_URL/?p=105" | grep "script src" && echo "✅ Scripts loaded"
```

**What this catches:**
- Theme not displaying content correctly
- Broken JavaScript
- Form submission issues
- CSS not applying

#### Verification Summary

Document verification results in README:

```bash
cat >> "$SESSION_DIR/README.md" <<EOF

**Verification Results:**
- Database: $([ $? -eq 0 ] && echo "✅ Match" || echo "❌ Mismatch")
- HTTP: $(grep -c "200" "$SESSION_DIR/http_verification.log") resources accessible
- Functional: ✅ All tests passed
EOF
```

---

### Step 7: Document Changes (MANDATORY)

**Every session requires a README documenting what was done.**

```bash
cat > "$SESSION_DIR/README.md" <<EOF
# Session: {Brief Description}

**Date:** $(date)
**WordPress Path:** /home/dave/skippy/rundaverun_local_site/app/public
**Site URL:** http://rundaverun-local-complete-022655.local
**Resources Modified:** Page 105 (Homepage)

**Changes Made:**
- Updated wellness center ROI from \$1.80 to \$2-3
- Fixed budget figure from \$110.5M to \$81M
- Updated hero image

**Status:** ✅ Completed successfully

**Files:**
- page_105_before.html - Original state
- page_105_v1.html - First edit (ROI fix)
- page_105_v2.html - Second edit (budget fix)
- page_105_v3.html - Third edit (image update)
- page_105_final.html - Final version applied
- page_105_after.html - Verified actual state after update
- http_verification.log - HTTP accessibility tests

**Verification:**
\`\`\`bash
# Database verification
diff page_105_final.html page_105_after.html
# (no differences - update successful)

# HTTP verification
curl -I http://rundaverun-local-complete-022655.local
# HTTP/1.1 200 OK
\`\`\`

**Rollback Procedure (if needed):**
\`\`\`bash
wp post update 105 --post_content="\$(cat $SESSION_DIR/page_105_before.html)"
\`\`\`
EOF
```

**README should include:**
- Brief description
- Date and time
- WordPress installation path and URL
- Resources modified (page IDs, file paths)
- List of specific changes
- Status (completed, blocked, partial)
- File manifest
- Verification results
- Rollback procedure

---

## Special Case: Binary/Media Files

**Binary files (images, videos, PDFs, archives) require different handling than text files.**

### Why Different?

- Large files shouldn't be versioned (`_v1`, `_v2`)
- Can't use `diff` to verify changes
- Focus on upload success and HTTP accessibility
- Thumbnails auto-generated by WordPress

### Media Upload Protocol

```bash
# 1. Create session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_media_upload"
mkdir -p "$SESSION_DIR"

# 2. Document source and metadata (not the files themselves if large)
cat > "$SESSION_DIR/manifest.txt" <<EOF
Source: /path/to/source/images/
File Count: 215
Types: JPEG
Total Size: 45MB
Method: WP-CLI media import
Destination: wp-content/uploads/2025/11/
EOF

# 3. Copy small sample for verification (5-10 files)
mkdir -p "$SESSION_DIR/samples/"
cp /path/to/source/sample*.jpg "$SESSION_DIR/samples/"

# 4. Execute upload and log results
wp media import /source/*.jpg --porcelain > "$SESSION_DIR/upload_ids.txt" 2>&1

# 5. Parse upload IDs
cat "$SESSION_DIR/upload_ids.txt" | grep -E '^[0-9]+$' > "$SESSION_DIR/media_ids.txt"
UPLOADED_COUNT=$(wc -l < "$SESSION_DIR/media_ids.txt")
echo "Uploaded: $UPLOADED_COUNT files" >> "$SESSION_DIR/manifest.txt"

# 6. HTTP verification - test sample images
FIRST_IMAGE_ID=$(head -1 "$SESSION_DIR/media_ids.txt")
IMAGE_URL=$(wp post get $FIRST_IMAGE_ID --field=guid)
curl -I "$IMAGE_URL" | grep "HTTP" >> "$SESSION_DIR/http_verification.log"

# Sample 10 random images for verification
shuf -n 10 "$SESSION_DIR/media_ids.txt" | while read ID; do
    URL=$(wp post get $ID --field=guid)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
    echo "ID $ID: $HTTP_CODE" >> "$SESSION_DIR/http_verification.log"
done

# 7. Document results
cat > "$SESSION_DIR/README.md" <<EOF
# Media Upload Session

**Date:** $(date)
**Source:** /path/to/source/images/
**Count:** $UPLOADED_COUNT files
**Destination:** wp-content/uploads/2025/11/

**Upload Status:** ✅ Complete
**HTTP Verification:** $(grep -c "200" "$SESSION_DIR/http_verification.log")/10 samples accessible

**Media IDs:** See media_ids.txt
**Upload Log:** See upload_ids.txt
EOF
```

### Key Differences for Binary Files

| Aspect | Text Files | Binary Files |
|--------|------------|--------------|
| Version iterations | `_v1`, `_v2`, `_v3` | No versioning |
| Verification | `diff` command | HTTP status codes |
| Storage | All versions saved | Sample only |
| Size concern | Low | High |
| Rollback | Restore previous version | Delete and re-upload |

---

## Special Case: Theme/Plugin Modifications

**Theme and plugin file modifications require careful backup procedures.**

### Why Different?

- Single file error can break entire site
- PHP syntax errors cause fatal errors
- Need full theme/plugin backup for safety
- Changes affect site-wide functionality

### Theme/Plugin Modification Protocol

```bash
# 1. Create session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/theme_mods/$(date +%Y%m%d_%H%M%S)_astra_child_featured_images"
mkdir -p "$SESSION_DIR"

# 2. Backup ENTIRE theme/plugin (safety measure)
THEME_PATH="/home/dave/skippy/rundaverun_local_site/app/public/wp-content/themes/astra-child"
cp -r "$THEME_PATH" "$SESSION_DIR/astra_child_full_backup/"

# 3. Save specific file being edited
cp "$THEME_PATH/functions.php" "$SESSION_DIR/functions_before.php"

# 4. Make edits (use code editor, not in-place edit)
# Edit file locally, save versions
cat "$SESSION_DIR/functions_before.php" > "$SESSION_DIR/functions_v1.php"
# (Add new code to functions_v1.php)

# 5. Create final version
cp "$SESSION_DIR/functions_v1.php" "$SESSION_DIR/functions_final.php"

# 6. Apply to live site
cp "$SESSION_DIR/functions_final.php" "$THEME_PATH/functions.php"

# 7. Verify - Check for PHP errors
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" eval "echo 'PHP syntax OK';" 2> "$SESSION_DIR/php_errors.log"

# If errors exist, ROLLBACK IMMEDIATELY
if [ -s "$SESSION_DIR/php_errors.log" ]; then
    echo "❌ PHP errors detected - ROLLING BACK"
    cp "$SESSION_DIR/functions_before.php" "$THEME_PATH/functions.php"
    cat "$SESSION_DIR/php_errors.log"
    exit 1
fi

# 8. HTTP verification
SITE_URL=$(wp --path="/home/dave/skippy/rundaverun_local_site/app/public" option get siteurl)
curl -I "$SITE_URL" | grep "HTTP/1.1 200" && echo "✅ Site accessible" || echo "❌ Site broken"

# 9. Document changes with diff
git diff --no-index "$SESSION_DIR/functions_before.php" "$SESSION_DIR/functions_final.php" > "$SESSION_DIR/changes.diff"

# 10. Save final state
cp "$THEME_PATH/functions.php" "$SESSION_DIR/functions_after.php"

# 11. Document
cat > "$SESSION_DIR/README.md" <<EOF
# Theme Modification: Astra Child Featured Images

**Date:** $(date)
**Theme:** astra-child
**File Modified:** functions.php
**Lines Changed:** $(wc -l < "$SESSION_DIR/changes.diff")

**Changes:**
- Added force_display_featured_images() function
- Added enable_featured_images_except_homepage() filter

**Verification:**
- PHP Syntax: ✅ No errors
- HTTP: ✅ Site accessible (200 OK)
- Functional: ✅ Featured images displaying

**Backups:**
- Full theme backup: astra_child_full_backup/
- Original functions.php: functions_before.php
- Final functions.php: functions_final.php

**Rollback Procedure:**
\`\`\`bash
cp $SESSION_DIR/functions_before.php $THEME_PATH/functions.php
\`\`\`
EOF
```

### Critical Safety Measures

**Before editing theme/plugin files:**

1. ✅ Create full backup of entire theme/plugin directory
2. ✅ Test PHP syntax after applying changes
3. ✅ Verify site still loads (HTTP 200)
4. ✅ Have rollback command ready
5. ✅ Keep browser window open to verify functionality

**Red flags requiring immediate rollback:**
- PHP fatal error
- White screen of death
- HTTP 500 error
- Site inaccessible

---

## Special Case: Database Modifications

**Direct database changes are risky and require extra precautions.**

### Why Different?

- No built-in versioning
- Changes can't be easily undone
- Single typo can corrupt data
- Affects multiple pages/posts simultaneously

### Database Modification Protocol

```bash
# 1. Create session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/db_mods/$(date +%Y%m%d_%H%M%S)_update_featured_images"
mkdir -p "$SESSION_DIR"

# 2. Export FULL database backup (before any changes)
wp db export "$SESSION_DIR/db_full_backup.sql"
echo "Full backup: $(du -h "$SESSION_DIR/db_full_backup.sql")"

# 3. Export affected tables specifically
wp db export "$SESSION_DIR/db_before_tables.sql" --tables=wp_posts,wp_postmeta

# 4. Document the query being run
cat > "$SESSION_DIR/query.sql" <<EOF
-- Update featured images for all policy pages
UPDATE wp_postmeta
SET meta_value = '1205'
WHERE post_id IN (699, 716, 717)
  AND meta_key = '_thumbnail_id';
EOF

# 5. Test query with SELECT first (dry run)
cat > "$SESSION_DIR/query_select.sql" <<EOF
-- Dry run - show what would be changed
SELECT post_id, meta_key, meta_value
FROM wp_postmeta
WHERE post_id IN (699, 716, 717)
  AND meta_key = '_thumbnail_id';
EOF

wp db query < "$SESSION_DIR/query_select.sql" > "$SESSION_DIR/query_before_result.txt"
echo "Rows to be affected:"
cat "$SESSION_DIR/query_before_result.txt"

# 6. Execute actual query
wp db query < "$SESSION_DIR/query.sql" 2>&1 | tee "$SESSION_DIR/query_result.log"

# 7. Verify with SELECT
wp db query < "$SESSION_DIR/query_select.sql" > "$SESSION_DIR/query_after_result.txt"

# 8. Compare before/after
diff "$SESSION_DIR/query_before_result.txt" "$SESSION_DIR/query_after_result.txt" > "$SESSION_DIR/query_diff.txt"

# 9. Export affected tables AFTER change
wp db export "$SESSION_DIR/db_after_tables.sql" --tables=wp_posts,wp_postmeta

# 10. Count affected rows
AFFECTED_ROWS=$(grep -c '_thumbnail_id' "$SESSION_DIR/db_after_tables.sql" || echo "0")
echo "Changed rows: $AFFECTED_ROWS" >> "$SESSION_DIR/query_result.log"

# 11. Functional verification - test pages load correctly
for ID in 699 716 717; do
    FEATURED_ID=$(wp post meta get $ID _thumbnail_id)
    echo "Page $ID featured image: $FEATURED_ID" >> "$SESSION_DIR/verification.log"
done

# 12. Document
cat > "$SESSION_DIR/README.md" <<EOF
# Database Modification: Update Featured Images

**Date:** $(date)
**Tables Affected:** wp_postmeta
**Records Modified:** $AFFECTED_ROWS

**Query:**
\`\`\`sql
$(cat "$SESSION_DIR/query.sql")
\`\`\`

**Verification:**
- Before state: query_before_result.txt
- After state: query_after_result.txt
- Differences: query_diff.txt

**Backups:**
- Full database: db_full_backup.sql (restore with: wp db import)
- Affected tables: db_before_tables.sql

**Rollback Procedure:**
\`\`\`bash
# Full restore (if needed)
wp db import $SESSION_DIR/db_full_backup.sql

# Or selective restore (just affected tables)
wp db import $SESSION_DIR/db_before_tables.sql
\`\`\`

**Status:** ✅ Completed successfully
EOF
```

### Database Safety Checklist

**Before running database modifications:**

- [ ] Full database backup exported
- [ ] Affected tables specifically backed up
- [ ] Query tested with SELECT first (dry run)
- [ ] Results reviewed before proceeding
- [ ] Rollback command prepared
- [ ] Verification query written

**After running database modifications:**

- [ ] Results logged
- [ ] Affected rows counted
- [ ] Before/after comparison documented
- [ ] Functional verification performed
- [ ] Rollback tested (in dev environment if possible)

---

## Verification Requirements

### Three-Level Verification Approach

All modifications should be verified at three levels:

#### Level 1: Database/Filesystem Verification

**Purpose:** Confirm changes were written correctly.

**Methods:**
- `diff` for text files
- `wp post get` for WordPress content
- `ls -la` for file permissions
- `md5sum` for file integrity

**Example:**
```bash
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"
# No output = files match = success
```

#### Level 2: HTTP Verification

**Purpose:** Confirm resources are accessible via web server.

**Methods:**
- `curl -I` for HTTP status codes
- `curl -s` for content retrieval
- `wget --spider` for accessibility testing

**Example:**
```bash
curl -I "http://site.local/uploads/image.jpg" | grep "HTTP"
# Should return: HTTP/1.1 200 OK
```

#### Level 3: Functional Verification

**Purpose:** Confirm changes work as intended.

**Methods:**
- Grep page output for expected content
- Test form submissions
- Verify JavaScript loads
- Check CSS applies

**Example:**
```bash
curl -s "http://site.local/?p=105" | grep "expected content"
# Should find the content
```

### Verification Decision Matrix

| Change Type | Database | HTTP | Functional |
|-------------|----------|------|------------|
| WordPress content | ✅ Required | ⚠️ Optional | ✅ Required |
| Media upload | ✅ Required | ✅ Required | ⚠️ Optional |
| Theme file | ⚠️ Optional | ✅ Required | ✅ Required |
| Plugin file | ⚠️ Optional | ✅ Required | ✅ Required |
| Database direct | ✅ Required | ⚠️ Optional | ✅ Required |
| Config file | ⚠️ Optional | ✅ Required | ✅ Required |

---

## File Naming Standards

### Session Directory Naming

**Format:** `{site}/{timestamp}_{description}`

**Examples:**
- `/home/dave/skippy/work/wordpress/rundaverun-local/20251112_043015_homepage_hero_image`
- `/home/dave/skippy/work/wordpress/theme_mods/20251112_044530_astra_child_featured_images`
- `/home/dave/skippy/work/scripts/20251112_050000_backup_script_enhancement`

**Rules:**
- Timestamp: `YYYYMMDD_HHMMSS`
- Description: lowercase, underscores, 2-5 words
- No spaces, no hyphens in description

### File Stage Naming

| Stage | Suffix | Purpose | Example |
|-------|--------|---------|---------|
| Original | `_before` | State before changes | `page_105_before.html` |
| Iteration 1 | `_v1` | First edit | `page_105_v1.html` |
| Iteration 2 | `_v2` | Second edit | `page_105_v2.html` |
| Iteration N | `_vN` | Nth edit | `page_105_v3.html` |
| Final | `_final` | Version to be applied | `page_105_final.html` |
| Verified | `_after` | State after applying | `page_105_after.html` |

### Content Type Naming

| Type | Format | Example |
|------|--------|---------|
| Pages | `page_{id}_{stage}.html` | `page_105_before.html` |
| Posts | `post_{id}_{stage}.html` | `post_941_v1.html` |
| Policies | `policy_{id}_{stage}.html` | `policy_699_final.html` |
| Theme files | `{filename}_{stage}.php` | `functions_before.php` |
| Database dumps | `db_{description}_{stage}.sql` | `db_full_backup.sql` |
| Logs | `{type}_log.txt` | `http_verification.log` |

---

## Cleanup & Archival

### Retention Policy

| Stage | Duration | Location | Action |
|-------|----------|----------|--------|
| Active | 30 days | `/home/dave/skippy/work/` | Keep all files |
| Archive | 90 days | Same location, compressed | Tar + gzip |
| Expired | Beyond 120 days | Deleted | Automatic cleanup |

### Manual Cleanup Procedures

#### Archive Old Sessions (After 30 Days)

```bash
# Find sessions older than 30 days
find /home/dave/skippy/work -type d -mtime +30 -name "20*_*"

# Archive each session
find /home/dave/skippy/work -type d -mtime +30 -name "20*_*" \
    -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;

# Verify archives created
find /home/dave/skippy/work -type f -name "*.tar.gz" -mtime -1
```

#### Delete Archived Sessions (After 120 Days)

```bash
# Find archives older than 120 days
find /home/dave/skippy/work -type f -name "*.tar.gz" -mtime +120

# Delete old archives
find /home/dave/skippy/work -type f -name "*.tar.gz" -mtime +120 -delete

# Log deletions
find /home/dave/skippy/work -type f -name "*.tar.gz" -mtime +120 \
    -printf "Deleted: %p\n" >> /home/dave/skippy/work/cleanup.log
```

#### Selective Cleanup (Keep Only Essential Files)

**Safe to delete immediately after verification:**

```bash
# Delete intermediate versions (keep _final and _after only)
find "$SESSION_DIR" -name "*_v[0-9].html" -delete
find "$SESSION_DIR" -name "*_v[0-9][0-9].html" -delete

# Delete large binary file samples (if upload succeeded)
if grep -q "✅ Complete" "$SESSION_DIR/README.md"; then
    rm -rf "$SESSION_DIR/samples/"
fi

# Delete temporary conversion files
find "$SESSION_DIR" -name "*_converted.*" -delete

# Keep:
# - _before files (rollback)
# - _final files (what was applied)
# - _after files (verification)
# - README.md (documentation)
# - *.log files (troubleshooting)
```

### Automated Cleanup Script

**Location:** `/home/dave/skippy/scripts/system/cleanup_work_files_v1.0.0.sh`

**Cron schedule:** Daily at 3 AM

```bash
#!/bin/bash
# Automated work files cleanup
# Runs daily at 3 AM via cron

WORK_DIR="/home/dave/skippy/work"
LOG_FILE="/home/dave/skippy/work/cleanup.log"

echo "$(date): Starting cleanup" >> "$LOG_FILE"

# Archive sessions older than 30 days
ARCHIVED=$(find "$WORK_DIR" -type d -mtime +30 -name "20*_*" -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \; -print | wc -l)
echo "Archived: $ARCHIVED sessions" >> "$LOG_FILE"

# Delete archives older than 120 days
DELETED=$(find "$WORK_DIR" -type f -name "*.tar.gz" -mtime +120 -delete -print | wc -l)
echo "Deleted: $DELETED archives" >> "$LOG_FILE"

echo "$(date): Cleanup complete" >> "$LOG_FILE"
```

---

## Protocol Compliance Checklist

Use this checklist for EVERY file modification session:

### Pre-Work
- [ ] Verified WordPress installation path (if WordPress work)
- [ ] Created session directory with timestamp
- [ ] Saved original state with `_before` suffix
- [ ] Session README template prepared

### During Work
- [ ] All intermediate files saved to `$SESSION_DIR`
- [ ] Each iteration versioned (`_v1`, `_v2`, etc.)
- [ ] NO files created in `/tmp/`
- [ ] Final version saved with `_final` suffix

### Post-Work Verification
- [ ] Database verification completed (if applicable)
- [ ] HTTP verification completed (if applicable)
- [ ] Functional verification completed (if applicable)
- [ ] Saved verified state with `_after` suffix
- [ ] Ran `diff` to confirm database changes

### Documentation
- [ ] README.md created with session summary
- [ ] Changes documented with before/after
- [ ] Verification results logged
- [ ] Rollback procedure documented
- [ ] Session directory path reported to user

### Safety
- [ ] Full backup exists (for risky changes)
- [ ] Rollback procedure tested (if critical change)
- [ ] No PHP errors (for theme/plugin changes)
- [ ] Site still accessible (HTTP 200)

---

## Common Mistakes to Avoid

### ❌ NEVER DO THIS

```bash
# Using /tmp/ for any files
python3 script.py > /tmp/output.html
wp post get 105 --field=post_content > /tmp/page.html
echo "data" > /tmp/temp.txt

# Skipping verification step
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"
# (Missing: save _after file and diff)

# Not saving original state
cat page.html | sed 's/old/new/g' > page.html  # Overwrites original!

# Working on wrong installation
wp media import image.jpg  # Which WordPress installation?
```

### ✅ ALWAYS DO THIS

```bash
# All files in session directory
python3 script.py > "$SESSION_DIR/output.html"
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"
echo "data" > "$SESSION_DIR/temp_data.txt"

# Complete verification
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# Save original before editing
cp page.html "$SESSION_DIR/page_before.html"
cat "$SESSION_DIR/page_before.html" | sed 's/old/new/g' > "$SESSION_DIR/page_v1.html"

# Verify installation path first
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" db check
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" media import image.jpg
```

---

## Quick Reference Card

### Essential Commands

```bash
# START EVERY SESSION
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# VERIFY WORDPRESS PATH (if applicable)
wp --path="/full/path/to/wordpress" db check

# SAVE ORIGINAL
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# SAVE ITERATIONS
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/g' > "$SESSION_DIR/page_105_v1.html"

# SAVE FINAL
cp "$SESSION_DIR/page_105_v1.html" "$SESSION_DIR/page_105_final.html"

# APPLY
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# VERIFY
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# DOCUMENT
cat > "$SESSION_DIR/README.md" <<EOF
# What Changed
...
EOF

# REPORT
echo "✅ Session complete: $SESSION_DIR"
```

### Path Variables

```bash
# Local WordPress installation
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"

# Work directory base
WORK_BASE="/home/dave/skippy/work"

# WP-CLI wrapper with path
alias wplocal="wp --path=$WP_PATH"
```

---

## Troubleshooting

### Issue: Files Not Accessible via HTTP (404)

**Symptoms:**
- Images uploaded successfully to database
- Files exist in filesystem
- HTTP requests return 404

**Root Cause:**
- Uploaded to wrong WordPress installation
- Wrong document root

**Solution:**
1. Verify installation path:
   ```bash
   cat ~/.config/Local/sites.json | python3 -m json.tool | grep -A 5 "path"
   ```
2. Check if files in correct location:
   ```bash
   ls -la /correct/path/wp-content/uploads/2025/11/
   ```
3. Copy files to correct location if needed
4. Verify HTTP accessibility:
   ```bash
   curl -I "http://site.local/wp-content/uploads/2025/11/image.jpg"
   ```

### Issue: Database Changes Not Reflecting

**Symptoms:**
- Query executed successfully
- No errors in log
- Changes not visible on site

**Root Cause:**
- Object cache not cleared
- Query syntax error (silent failure)
- Wrong table prefix

**Solution:**
1. Check query syntax:
   ```bash
   cat "$SESSION_DIR/query.sql"
   ```
2. Test with SELECT first:
   ```bash
   wp db query < "$SESSION_DIR/query_select.sql"
   ```
3. Clear WordPress cache:
   ```bash
   wp cache flush
   ```
4. Verify table prefix:
   ```bash
   wp db tables --all-tables
   ```

### Issue: Theme File Changes Break Site

**Symptoms:**
- White screen of death
- HTTP 500 error
- PHP fatal error

**Root Cause:**
- PHP syntax error
- Missing semicolon/bracket
- Function name collision

**Solution:**
1. **IMMEDIATELY rollback:**
   ```bash
   cp "$SESSION_DIR/functions_before.php" "$THEME_PATH/functions.php"
   ```
2. Check PHP syntax:
   ```bash
   php -l "$SESSION_DIR/functions_final.php"
   ```
3. Review error log:
   ```bash
   tail -f /path/to/error.log
   ```
4. Fix syntax error, test again

---

## Protocol Version Comparison

| Feature | v1.0 | v2.0 | v2.1 |
|---------|------|------|------|
| Session directories | ✅ | ✅ | ✅ |
| 7-step process | ❌ | ✅ | ✅ |
| Installation verification | ❌ | ❌ | ✅ |
| HTTP verification | ❌ | ⚠️ Partial | ✅ |
| Binary file handling | ❌ | ❌ | ✅ |
| Theme/plugin procedures | ❌ | ❌ | ✅ |
| Database procedures | ❌ | ❌ | ✅ |
| Functional verification | ❌ | ❌ | ✅ |
| Cleanup/archival | ⚠️ Basic | ⚠️ Basic | ✅ |

---

## Related Documentation

- `/home/dave/skippy/.claude/CLAUDE.md` - Quick reference protocol
- `/home/dave/skippy/documentation/protocols/auto_compact_recovery_protocol.md` - Git recovery procedures
- `/home/dave/skippy/conversations/protocol_gap_analysis_2025-11-12.md` - Protocol weakness analysis
- `/home/dave/skippy/conversations/site_consolidation_complete_2025-11-12.md` - Real-world protocol failure case study

---

## Changelog

### Version 2.1 (November 12, 2025)

**Added:**
- Step 0: Installation path verification for WordPress work
- Enhanced Step 6 with three-level verification (database, HTTP, functional)
- Binary/media file protocol section
- Theme/plugin modification protocol section
- Database modification protocol section
- Verification requirements matrix
- Cleanup and archival procedures
- Troubleshooting section

**Changed:**
- Updated all WordPress path examples from "Local Sites" to `rundaverun_local_site`
- Enhanced verification examples with HTTP testing
- Improved README.md templates with verification results

**Fixed:**
- Critical path verification issue that caused 404 errors on media uploads

### Version 2.0 (November 8, 2025)

**Added:**
- 7-step mandatory process (Steps 1-7)
- WordPress-specific examples
- Complete workflow examples
- Pre-flight checklist

### Version 1.0 (October 2025)

**Initial release:**
- Session directory concept
- File naming standards
- Basic retention policy

---

**Protocol Status:** ✅ Active and Production-Ready

**Last Tested:** November 12, 2025 (Media upload and consolidation session)

**Compliance:** Mandatory for all file modification work
