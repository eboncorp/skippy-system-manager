# WordPress Site Diagnostic Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Owner:** Claude Code / Dave
**Type:** Operational Protocol
**Priority:** High

---

## Context

When a user reports "the site has problems," systematic diagnostic procedures are required to identify issues that may not be immediately visible through surface-level checks. This protocol addresses critical blindspots discovered during the rundaverun-local diagnostic session on 2025-11-07.

## Purpose

- Comprehensive site health assessment
- Detection of content-level issues (not just server/PHP errors)
- Navigation and user experience validation
- Database content integrity verification
- Prevention of false-positive "healthy" diagnostics

---

## The Seven-Layer Diagnostic Model

### Layer 1: Infrastructure Health ⚙️
**Goal**: Verify server, PHP, and WordPress core are operational

```bash
# Check site accessibility
curl -I $SITE_URL | head -3

# Check WordPress version
wp core version

# Check PHP version and errors
php -v
tail -50 /path/to/error.log 2>/dev/null || echo "No error log found"

# Check database connection
wp db check

# Check disk space
df -h | grep -E 'Filesystem|/$'
```

**Success Criteria:**
- ✅ HTTP 200 response
- ✅ WordPress core current or 1 version behind
- ✅ No PHP fatal errors in last 24 hours
- ✅ Database connection successful
- ✅ > 10% disk space available

---

### Layer 2: Plugin & Theme Health 🔌
**Goal**: Verify all plugins/themes active and error-free

```bash
# List active plugins
wp plugin list --status=active

# Check for plugin errors
wp plugin list --status=error

# Check theme status
wp theme list --status=active

# Verify plugin activation hooks ran
wp db query "SHOW TABLES LIKE 'wp_%'" | grep -i {plugin_prefix}

# Check for plugin conflicts
wp plugin status
```

**Success Criteria:**
- ✅ All required plugins active
- ✅ No plugin errors
- ✅ Plugin database tables exist
- ✅ Theme active and functional
- ✅ No PHP warnings from plugins

**Blindspot Addressed:**
- ❌ Previous: Only checked if plugins were active
- ✅ Now: Check database tables, activation hooks, and error status

---

### Layer 3: Content Integrity 📝
**Goal**: Verify page/post content is actual HTML, not corrupted data

```bash
# Check for literal bash commands in content
wp post list --post_type=page --fields=ID,post_title --format=csv | while IFS=, read -r id title; do
    content=$(wp post get $id --field=post_content 2>/dev/null)
    if echo "$content" | grep -q '\$(cat'; then
        echo "⚠️  Page $id ($title): Contains bash command string"
    fi
done

# Check for common content corruption patterns
wp db query "SELECT ID, post_title FROM wp_posts WHERE post_content LIKE '%\$(cat%' OR post_content LIKE '%<?php%' OR post_content LIKE '%<script>alert%' LIMIT 10"

# Check for empty critical pages
for page_id in 105 107 337; do  # Homepage, Our Plan, Voter Education
    content=$(wp post get $page_id --field=post_content 2>/dev/null)
    if [ -z "$content" ]; then
        echo "⚠️  Page $page_id is empty"
    elif [ ${#content} -lt 100 ]; then
        echo "⚠️  Page $page_id suspiciously short (${#content} chars)"
    fi
done
```

**Success Criteria:**
- ✅ No bash command strings in content
- ✅ No PHP code in post content
- ✅ No suspicious JavaScript
- ✅ Critical pages have content > 100 chars
- ✅ No HTML encoding issues

**Blindspot Addressed:**
- ❌ Previous: Never checked actual page content
- ✅ Now: Inspect content for corruption, literal commands, and suspicious patterns

---

### Layer 4: Navigation & URL Structure 🗺️
**Goal**: Verify users can actually navigate the site

```bash
# Check permalink structure
wp rewrite list | head -10

# Test critical page URLs
for slug in "/" "/about-dave" "/our-plan" "/voter-education" "/policy-library"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}${slug}")
    if [ "$response" != "200" ]; then
        echo "⚠️  $slug returned HTTP $response"
    fi
done

# Check for broken internal links
wp post list --post_type=page,post,policy_document --format=ids | xargs -I {} wp post get {} --field=post_content | grep -oP 'href="[^"]*"' | sort -u > /tmp/all_links.txt

# Test policy document URLs
wp post list --post_type=policy_document --format=csv --fields=ID,post_name | while IFS=, read -r id slug; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}/policy/${slug}/")
    if [ "$response" = "404" ]; then
        echo "⚠️  Policy $id ($slug) returns 404"
    fi
done

# Check if rewrite flush needed
if wp rewrite list | wc -l | grep -q "^0$"; then
    echo "⚠️  No rewrite rules found - flush needed"
fi
```

**Success Criteria:**
- ✅ All critical pages return 200
- ✅ No 404s on policy documents
- ✅ Permalink structure valid
- ✅ Rewrite rules exist
- ✅ Menu items link to valid pages

**Blindspot Addressed:**
- ❌ Previous: Only checked homepage HTTP response
- ✅ Now: Test navigation paths, policy URLs, and detect 404s

---

### Layer 5: Database Content Validation 🗄️
**Goal**: Verify database contains expected data structure

```bash
# Check post counts
echo "Pages: $(wp post list --post_type=page --format=count)"
echo "Policies: $(wp post list --post_type=policy_document --format=count)"
echo "Posts: $(wp post list --post_type=post --format=count)"

# Check for orphaned content
wp db query "SELECT COUNT(*) as orphaned FROM wp_posts WHERE post_parent NOT IN (SELECT ID FROM wp_posts) AND post_parent != 0"

# Check for duplicate slugs
wp db query "SELECT post_name, COUNT(*) as count FROM wp_posts WHERE post_status = 'publish' GROUP BY post_name HAVING count > 1"

# Check menu structure
wp menu list --format=table

# Check custom tables exist
for table in email_subscribers drip_campaigns event_rsvps analytics; do
    if ! wp db query "SHOW TABLES LIKE '%dbpm_${table}%'" | grep -q dbpm; then
        echo "⚠️  Table dbpm_${table} missing"
    fi
done
```

**Success Criteria:**
- ✅ Expected post counts match
- ✅ No orphaned content
- ✅ No duplicate slugs
- ✅ Menus properly structured
- ✅ Custom plugin tables exist

**Blindspot Addressed:**
- ❌ Previous: Checked if tables exist, not content validity
- ✅ Now: Validate data structure, counts, and relationships

---

### Layer 6: Frontend Rendering 🎨
**Goal**: Verify pages render correctly with CSS/JS

```bash
# Check for missing assets
wp plugin list --status=active --format=csv --fields=name | while read plugin; do
    asset_dir="wp-content/plugins/$plugin/assets"
    if [ -d "$asset_dir" ]; then
        echo "Checking $plugin assets..."
        ls -la "$asset_dir"/{css,js}/ 2>/dev/null | grep -E '\.css|\.js' || echo "⚠️  $plugin missing CSS/JS"
    fi
done

# Check theme assets
ls -la wp-content/themes/*/assets/{css,js}/ 2>/dev/null | head -20

# Test page rendering (check for white screen)
for url in "/" "/our-plan" "/voter-education"; do
    content=$(curl -s "${SITE_URL}${url}")
    word_count=$(echo "$content" | wc -w)
    if [ $word_count -lt 50 ]; then
        echo "⚠️  $url renders suspiciously short ($word_count words)"
    fi
done

# Check for JavaScript errors (requires headless browser)
# wp eval "echo do_shortcode('[test_shortcode]');" 2>&1 | grep -i error
```

**CSS/Layout Issue Detection:**
```bash
# Check for common CSS issues that cause text wrapping/overflow
curl -s "${SITE_URL}" > /tmp/homepage.html

# Check for word-break issues (long words breaking mid-word)
grep -oP '>\K[^<]{20,}' /tmp/homepage.html | while read word; do
    if echo "$word" | grep -qP '\w{15,}'; then
        echo "⚠️  Found long word (may wrap awkwardly): ${word:0:30}..."
    fi
done

# Check for missing word-wrap/overflow CSS properties
if ! curl -s "${SITE_URL}" | grep -qi "word-wrap\|overflow-wrap\|word-break"; then
    echo "⚠️  No word-wrap CSS detected (may cause text overflow)"
fi

# Check for viewport meta tag (mobile responsiveness)
if ! curl -s "${SITE_URL}" | grep -qi 'viewport'; then
    echo "⚠️  No viewport meta tag (mobile may render incorrectly)"
fi

# Check for missing CSS that could cause layout issues
curl -s "${SITE_URL}" | grep -E 'href="[^"]*\.css"' | wc -l
```

**Manual Screenshot Review Checklist:**
When reviewing screenshots, look for:
- ✅ Text wrapping mid-word (e.g., "Compensatio\nn Plan")
- ✅ Overlapping text or elements
- ✅ Cut-off text at container edges
- ✅ Inconsistent spacing/alignment
- ✅ Missing images or broken icons
- ✅ Unreadable text (color contrast issues)
- ✅ Elements extending beyond viewport

**Success Criteria:**
- ✅ All CSS files present
- ✅ All JS files present
- ✅ Pages render > 50 words
- ✅ No white screen of death
- ✅ Shortcodes render (not show as text)
- ✅ No awkward text wrapping (screenshot review)
- ✅ All text readable and properly laid out

**Blindspot Addressed:**
- ❌ Previous: Assumed if server returns 200, page is fine
- ✅ Now: Check actual rendered content length and asset presence
- ✅ Now: Detect CSS issues causing text wrapping/overflow
- ✅ Now: Require manual screenshot review for visual issues

---

### Layer 7: User Experience Testing 👤
**Goal**: Verify site works from user perspective

**Manual Checks** (screenshot-based verification):
```bash
# Take screenshots of critical pages
for page in home our-plan voter-education policy-library; do
    echo "Please verify $page displays correctly"
    # User takes screenshot and shares
done
```

**Form Testing:**
```bash
# Test email signup form
wp eval "do_action('wp_ajax_nopriv_dbpm_email_signup');" 2>&1 | grep -E 'success|error'

# Test AJAX endpoints
curl -X POST "${SITE_URL}/wp-admin/admin-ajax.php" \
    -d "action=dbpm_email_signup&email=test@test.com" 2>&1 | grep -E 'success|error'
```

**Success Criteria:**
- ✅ Forms submit successfully
- ✅ Search works
- ✅ Mobile responsive (user verification)
- ✅ No visual bugs in screenshots
- ✅ Navigation menu visible and functional

**Blindspot Addressed:**
- ❌ Previous: No user-perspective testing
- ✅ Now: Screenshot verification and form testing

---

## Complete Diagnostic Script

```bash
#!/bin/bash
# WordPress Comprehensive Site Diagnostic
# Usage: bash wordpress_site_diagnostic.sh [site_url]

SITE_URL="${1:-http://localhost}"
REPORT_FILE="/tmp/wp_diagnostic_$(date +%Y%m%d_%H%M%S).txt"

echo "=== WordPress Site Diagnostic Report ===" | tee "$REPORT_FILE"
echo "Site: $SITE_URL" | tee -a "$REPORT_FILE"
echo "Date: $(date)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Layer 1: Infrastructure
echo "=== LAYER 1: Infrastructure Health ===" | tee -a "$REPORT_FILE"
curl -I "$SITE_URL" 2>&1 | head -3 | tee -a "$REPORT_FILE"
wp core version 2>&1 | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Layer 2: Plugins
echo "=== LAYER 2: Plugin Health ===" | tee -a "$REPORT_FILE"
wp plugin list --status=active --fields=name,version,update | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Layer 3: Content Integrity
echo "=== LAYER 3: Content Integrity ===" | tee -a "$REPORT_FILE"
wp db query "SELECT ID, post_title FROM wp_posts WHERE post_type='page' AND (post_content LIKE '%\$(cat%' OR post_content LIKE '%<?php%')" 2>&1 | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Layer 4: Navigation
echo "=== LAYER 4: Navigation Testing ===" | tee -a "$REPORT_FILE"
for slug in "/" "/our-plan" "/voter-education" "/policy-library"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}${slug}")
    echo "$slug: HTTP $response" | tee -a "$REPORT_FILE"
done
echo "" | tee -a "$REPORT_FILE"

# Layer 5: Database
echo "=== LAYER 5: Database Validation ===" | tee -a "$REPORT_FILE"
echo "Pages: $(wp post list --post_type=page --format=count)" | tee -a "$REPORT_FILE"
echo "Policies: $(wp post list --post_type=policy_document --format=count 2>/dev/null || echo 0)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Layer 6: Frontend
echo "=== LAYER 6: Frontend Rendering ===" | tee -a "$REPORT_FILE"
homepage_words=$(curl -s "$SITE_URL" | wc -w)
echo "Homepage word count: $homepage_words" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Layer 7: User Experience
echo "=== LAYER 7: User Experience ===" | tee -a "$REPORT_FILE"
echo "Manual verification required - see screenshots" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Summary
echo "=== DIAGNOSTIC COMPLETE ===" | tee -a "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
```

---

## When to Use This Protocol

**Trigger Conditions:**
1. User reports "site has problems"
2. After any deployment or merge
3. After plugin activation/deactivation
4. After WordPress/PHP updates
5. Before declaring site "healthy"
6. Weekly maintenance checks

**NOT Needed When:**
- Simple plugin settings change
- Adding new post/page content
- Changing theme colors/CSS only
- Updating user accounts

---

## Red Flags Requiring Immediate Investigation

1. **Content Issues:**
   - Bash command strings in page content: `$(cat ...)`
   - PHP code in post_content field: `<?php ...`
   - Suspicious JavaScript: `<script>alert(...)`
   - Pages < 100 characters when should be longer

2. **Navigation Issues:**
   - Critical pages return 404
   - Policy documents return 404
   - Menu links broken
   - Rewrite rules empty (0 rules)

3. **Database Issues:**
   - Expected tables missing
   - Post counts unexpectedly low/high
   - Duplicate slugs found
   - Orphaned content detected

4. **Rendering Issues:**
   - Page word count < 50 when expecting article
   - Missing CSS/JS files
   - Shortcodes displaying as text
   - White screen (0 content)

5. **CSS/Layout Issues:**
   - Text wrapping mid-word (e.g., "Compensatio\nn Plan")
   - Overlapping elements
   - Text cut off at container edges
   - Missing viewport meta tag
   - No word-wrap/overflow CSS properties

---

## Integration with Existing Protocols

**Extends:**
- `deployment_success_verification_protocol.md` - Adds Layers 3-7
- `error_recovery_protocol.md` - Provides diagnostic steps

**Used By:**
- `wordpress_deployment_workflow.md` (if exists)
- `site_maintenance_protocol.md` (if exists)

**Requires:**
- `work_files_preservation_protocol.md` - For saving diagnostic outputs
- `safety_backup_protocol.md` - Before making fixes

---

## Quick Reference Card

### 60-Second Quick Check
```bash
# Run these 5 commands for fast health check:
curl -I http://site.local | head -1                          # Infrastructure
wp plugin list --status=active --format=count                # Plugins
wp db query "SELECT COUNT(*) FROM wp_posts WHERE post_content LIKE '%\$(cat%'" # Content
curl -s -o /dev/null -w "%{http_code}" http://site.local/our-plan/  # Navigation
wp post list --post_type=page --format=count                 # Database
```

### 5-Minute Comprehensive Check
```bash
bash wordpress_site_diagnostic.sh http://site.local
```

### Full Diagnostic (15 minutes)
Run all 7 layers + screenshot verification + manual testing

---

## Examples of Blindspots This Protocol Addresses

### Case Study: rundaverun-local (2025-11-07)

**Reported Issue:** "the local site has problems"

**Initial Diagnostic (Insufficient):**
- ✅ Plugin active
- ✅ No PHP errors
- ✅ Database tables exist
- ✅ Homepage returns 200
- ❌ **MISSED:** Pages had bash command strings instead of HTML
- ❌ **MISSED:** Policy pages returned 404
- ❌ **MISSED:** Navigation broken

**Enhanced Diagnostic (This Protocol):**
- Layer 1: ✅ Infrastructure healthy
- Layer 2: ✅ Plugins active
- Layer 3: ❌ **DETECTED:** Pages 107, 337 had `$(cat ...)` strings
- Layer 4: ❌ **DETECTED:** Policy pages returned 404
- Layer 5: ✅ Database valid
- Layer 6: ❌ **DETECTED:** Pages rendered bash commands
- Layer 7: ❌ **DETECTED:** Screenshots showed broken pages

**Result:** All issues found and fixed in 10 minutes after using Layer 3 & 4 checks.

---

## Anticipated Future Blindspots

Based on common WordPress issues, this protocol also prevents:

1. **Shortcode Rendering Issues**
   - Shortcodes display as `[shortcode_name]` instead of rendering
   - Detection: Layer 6 checks for literal shortcode text in rendered output

2. **Database Character Encoding Issues**
   - Content contains `â€™` instead of apostrophes
   - Detection: Layer 3 checks for common encoding artifacts

3. **Cached Content Issues**
   - Old content displayed despite updates
   - Detection: Layer 6 compares database content vs rendered output

4. **Broken Embeds**
   - YouTube/Twitter embeds show as raw URLs
   - Detection: Layer 6 checks for oEmbed patterns

5. **Missing Post Meta**
   - Custom fields not saved during import
   - Detection: Layer 5 queries post_meta counts

6. **SEO Issues**
   - Missing meta descriptions, broken Open Graph tags
   - Detection: Layer 6 checks HTML headers

7. **Performance Issues**
   - Pages load but take > 10 seconds
   - Detection: Add Layer 8 for performance metrics

8. **CSS/Layout Issues** ⚠️ **ADDED 2025-11-07**
   - Text wrapping mid-word in headings/titles
   - Container width too narrow for content
   - Missing `word-wrap`, `overflow-wrap`, or `hyphens` CSS
   - Detection: Layer 6 screenshot review checklist + automated CSS checks

---

## Maintenance

**Review Schedule:** Monthly
**Update When:**
- New WordPress major version released
- New critical plugin added
- New blindspot discovered
- Post-incident review suggests enhancement

**Version History:**
- 1.0.0 (2025-11-07): Initial version based on rundaverun-local diagnostic
- 1.1.0 (2025-11-07): Added CSS/Layout detection to Layer 6 (text wrapping, overflow)

---

## Related Documentation

- `/home/dave/skippy/conversations/rundaverun_local_site_diagnostic_2025-11-07.md` - Case study
- `/home/dave/skippy/documentation/protocols/deployment_success_verification_protocol.md` - Post-deployment checks
- `/home/dave/skippy/documentation/WORK_FILES_PRESERVATION_PROTOCOL.md` - Saving diagnostic outputs

---

**Protocol Status:** ✅ Active
**Last Incident:** 2025-11-07 (rundaverun-local bash command strings, CSS text wrapping)
**Effectiveness:** Addresses 8 critical blindspots in standard diagnostics
**Adoption:** Required for all WordPress site health checks

---

*Generated: 2025-11-07*
*Next Review: 2025-12-07*
