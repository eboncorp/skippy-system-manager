# Shell Command Syntax & Code Exposure Scan
**Date:** November 4, 2025
**WordPress Site:** rundaverun-local.local
**Database:** local (prefix: wp_7e1ce15f22_)
**Total posts scanned:** 443 published posts

---

## CRITICAL ISSUES FOUND

**SEVERITY:** HIGH - Shell command syntax is being displayed as literal text instead of executing or being replaced with HTML content.

**ROOT CAUSE:** Failed command substitution - `$(cat /tmp/file.html)` patterns were inserted into post content but never executed/replaced, causing them to display as literal text on the website.

---

## AFFECTED POSTS

### Issue #1: Post 106 - "About Dave" (page)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post106_policy_count_fixed.html)
```

**Chain of Nested Commands:**
- post106_policy_count_fixed.html → contains `$(cat /tmp/post106_styles_fixed.html)`
- post106_styles_fixed.html → contains actual HTML content (7,958 bytes)

**Correct Content Available:** `/tmp/post106_styles_fixed.html` (7.8 KB)
**Status:** Backup file exists with complete HTML

---

### Issue #2: Post 107 - "Our Plan" (page)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post107_budget_fixed.html)
```

**Chain of Nested Commands:**
- post107_budget_fixed.html → contains `$(cat /tmp/post107_fixed.html)`
- post107_fixed.html → contains actual HTML content (5,659 bytes)

**Correct Content Available:** `/tmp/post107_fixed.html` (5.5 KB)
**Status:** Backup file exists with complete HTML

---

### Issue #3: Post 109 - "Contact" (page)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post109_fixed.html)
```

**Chain of Nested Commands:**
- post_109.html → contains `$(cat /tmp/post109_fixed.html)` (31 bytes - nested command)
- post109_fixed.html → contains actual HTML content (4,410 bytes)

**Correct Content Available:** `/tmp/post109_fixed.html` (4.3 KB)
**Status:** Backup file exists with complete HTML

---

### Issue #4: Post 151 - "7. Research Bibliography & Citations" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post151_fixed.html)
```

**Correct Content Available:** `/tmp/post151_fixed.html` (30,905 bytes)
**Status:** Backup file exists with complete HTML

---

### Issue #5: Post 245 - "15. ABOUT DAVE BIGGERS" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post245_fixed.html)
```

**Correct Content Available:** `/tmp/post245_fixed.html` (9,799 bytes)
**Status:** Backup file exists with complete HTML

---

### Issue #6: Post 249 - "18. OUR PLAN FOR LOUISVILLE" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post249_fixed.html)
```

**Correct Content Available:** `/tmp/post249_fixed.html` (16,613 bytes)
**Status:** Backup file exists with complete HTML

---

### Issue #7: Post 328 - "Complete Voter Education Glossary" (page)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post328_fixed.html)
```

**Correct Content Available:** `/tmp/post328_fixed.html` (2,112 bytes)
**Status:** Backup file exists with complete HTML

---

### Issue #8: Post 699 - "19. Public Safety & Community Policing" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post699_budget_fixed.html)
<hr />
<h2 id="related-policies">RELATED POLICIES</h2>
[...continues with HTML...]
```

**Chain of Nested Commands:**
- post699_budget_fixed.html → contains `$(cat /tmp/post699_fixed.html)` (31 bytes - nested command)
- post699_fixed.html → contains actual HTML content (45,928 bytes)

**Correct Content Available:** `/tmp/post699_fixed.html` (45 KB)
**Additional Content:** The post has some HTML after the shell command, suggesting partial restoration was attempted
**Status:** Backup file exists with complete HTML

---

### Issue #9: Post 700 - "20. Criminal Justice Reform" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post700_fixed.html)
<hr />
<h2 id="related-policies">RELATED POLICIES</h2>
[...continues with HTML...]
```

**Correct Content Available:** `/tmp/post700_fixed.html` (23,239 bytes)
**Additional Content:** The post has some HTML after the shell command
**Status:** Backup file exists with complete HTML

---

### Issue #10: Post 716 - "21. Health & Human Services" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post716_budget_real_fix.html)
<hr />
<h2 id="related-policies">RELATED POLICIES</h2>
[...continues with HTML...]
```

**Chain of Nested Commands:**
- post716_budget_real_fix.html → contains `$(cat /tmp/post716_budget_fixed.html)` (38 bytes - nested)
- post716_budget_fixed.html → contains `$(cat /tmp/post716_fixed.html)` (31 bytes - nested)
- post716_fixed.html → contains actual HTML content (29,744 bytes)

**Correct Content Available:** `/tmp/post716_fixed.html` (29 KB)
**Status:** Backup file exists with complete HTML

---

### Issue #11: Post 717 - "34. Economic Development & Jobs" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post717_fixed.html)
<hr />
<h2 id="related-policies">RELATED POLICIES</h2>
[...continues with HTML...]
```

**Correct Content Available:** `/tmp/post717_fixed.html` (117,513 bytes / 115 KB)
**Status:** Backup file exists with complete HTML

---

### Issue #12: Post 934 - "Volunteer Dashboard" (page)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post934_fixed.html)
```

**Correct Content Available:** `/tmp/post934_fixed.html` (3,346 bytes)
**Status:** Backup file exists with complete HTML

---

### Issue #13: Post 941 - "Phone Banking Script" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post941_fixed.html)
```

**Correct Content Available:** `/tmp/post941_fixed.html` (3,038 bytes)
**Status:** Backup file exists with complete HTML

---

### Issue #14: Post 942 - "Canvassing Talking Points" (policy_document)
**Type:** Shell command syntax exposed
**Current Content:**
```
$(cat /tmp/post942_fixed.html)
```

**Correct Content Available:** `/tmp/post942_fixed.html` (5,104 bytes)
**Status:** Backup file exists with complete HTML

---

## SUMMARY

- **Total published posts:** 443
- **Total issues found:** 14 posts
- **Shell command syntax:** 14 posts (100% of issues)
- **Nested shell commands:** 6 posts have multiple levels of nesting
- **PHP code exposed:** 0
- **File paths exposed:** 14 (all /tmp/ references)
- **Temp file references:** 14

### Breakdown by Post Type:
- **Pages:** 4 (Posts 106, 107, 109, 328, 934)
- **Policy Documents:** 9 (Posts 151, 245, 249, 699, 700, 716, 717, 941, 942)

### Severity Assessment:
- **CRITICAL:** All 14 posts show shell command syntax to public visitors
- **HIGH IMPACT:** Includes key pages (About Dave, Our Plan, Contact)
- **USER EXPERIENCE:** Visitors see literal `$(cat /tmp/...)` text instead of content
- **SECURITY CONCERN:** Exposes internal file system paths (/tmp/)
- **PROFESSIONAL IMPACT:** Makes site appear broken/unprofessional

---

## NESTED COMMAND CHAINS DISCOVERED

Some posts have multiple layers of shell command substitution that never executed:

1. **Post 106 (2 levels deep):**
   - Database → `post106_policy_count_fixed.html`
   - → `post106_styles_fixed.html` (actual content)

2. **Post 107 (2 levels deep):**
   - Database → `post107_budget_fixed.html`
   - → `post107_fixed.html` (actual content)

3. **Post 109 (2 levels deep):**
   - Database → `post109_fixed.html` (actual content)
   - But `/tmp/post_109.html` has nested command too

4. **Post 699 (2 levels deep):**
   - Database → `post699_budget_fixed.html`
   - → `post699_fixed.html` (actual content)

5. **Post 716 (3 levels deep - MOST COMPLEX):**
   - Database → `post716_budget_real_fix.html`
   - → `post716_budget_fixed.html`
   - → `post716_fixed.html` (actual content)

---

## TEMP FILES INVENTORY

All backup files are available in `/tmp/` with complete HTML content ready for restoration:

### Complete Backup Files (with actual HTML content):
```bash
# Pages
/tmp/post106_styles_fixed.html       7,958 bytes   ✓ READY
/tmp/post107_fixed.html              5,659 bytes   ✓ READY
/tmp/post109_fixed.html              4,410 bytes   ✓ READY
/tmp/post328_fixed.html              2,112 bytes   ✓ READY
/tmp/post934_fixed.html              3,346 bytes   ✓ READY

# Policy Documents
/tmp/post151_fixed.html             30,905 bytes   ✓ READY
/tmp/post245_fixed.html              9,799 bytes   ✓ READY
/tmp/post249_fixed.html             16,613 bytes   ✓ READY
/tmp/post699_fixed.html             45,928 bytes   ✓ READY
/tmp/post700_fixed.html             23,239 bytes   ✓ READY
/tmp/post716_fixed.html             29,744 bytes   ✓ READY
/tmp/post717_fixed.html            117,513 bytes   ✓ READY
/tmp/post941_fixed.html              3,038 bytes   ✓ READY
/tmp/post942_fixed.html              5,104 bytes   ✓ READY
```

### Nested Command Files (DO NOT USE - contain shell commands):
```bash
/tmp/post106_policy_count_fixed.html     38 bytes   ✗ CONTAINS: $(cat /tmp/post106_styles_fixed.html)
/tmp/post107_budget_fixed.html           31 bytes   ✗ CONTAINS: $(cat /tmp/post107_fixed.html)
/tmp/post_109.html                       31 bytes   ✗ CONTAINS: $(cat /tmp/post109_fixed.html)
/tmp/post699_budget_fixed.html           31 bytes   ✗ CONTAINS: $(cat /tmp/post699_fixed.html)
/tmp/post716_budget_real_fix.html        38 bytes   ✗ CONTAINS: $(cat /tmp/post716_budget_fixed.html)
/tmp/post716_budget_fixed.html           31 bytes   ✗ CONTAINS: $(cat /tmp/post716_fixed.html)
```

### Additional Backup Files Available:
```bash
# These are complete backups that could be used as alternatives
/tmp/post_106_fixed.html             8,042 bytes   ✓ ALTERNATIVE
/tmp/post_106.html                   8,043 bytes   ✓ ALTERNATIVE
/tmp/post_699.html                  45,925 bytes   ✓ ALTERNATIVE
/tmp/post_716.html                      31 bytes   ✗ Contains shell command
/tmp/post_717.html                      31 bytes   ✗ Contains shell command
```

---

## RECOMMENDED FIX PROCEDURE

### Method 1: WP-CLI Bulk Update (FASTEST)
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Update each post with correct content
wp post update 106 --post_content="$(cat /tmp/post106_styles_fixed.html)" --allow-root
wp post update 107 --post_content="$(cat /tmp/post107_fixed.html)" --allow-root
wp post update 109 --post_content="$(cat /tmp/post109_fixed.html)" --allow-root
wp post update 151 --post_content="$(cat /tmp/post151_fixed.html)" --allow-root
wp post update 245 --post_content="$(cat /tmp/post245_fixed.html)" --allow-root
wp post update 249 --post_content="$(cat /tmp/post249_fixed.html)" --allow-root
wp post update 328 --post_content="$(cat /tmp/post328_fixed.html)" --allow-root
wp post update 699 --post_content="$(cat /tmp/post699_fixed.html)" --allow-root
wp post update 700 --post_content="$(cat /tmp/post700_fixed.html)" --allow-root
wp post update 716 --post_content="$(cat /tmp/post716_fixed.html)" --allow-root
wp post update 717 --post_content="$(cat /tmp/post717_fixed.html)" --allow-root
wp post update 934 --post_content="$(cat /tmp/post934_fixed.html)" --allow-root
wp post update 941 --post_content="$(cat /tmp/post941_fixed.html)" --allow-root
wp post update 942 --post_content="$(cat /tmp/post942_fixed.html)" --allow-root
```

### Method 2: Direct Database Update (FOR VERIFICATION)
```bash
# Verify the current broken state
wp db query "SELECT ID, post_title, LEFT(post_content, 80) FROM wp_7e1ce15f22_posts WHERE post_status='publish' AND post_content LIKE '%\$(cat%'" --allow-root
```

### Method 3: Create Restoration Script
```bash
#!/bin/bash
# restore_posts.sh
cd "/home/dave/Local Sites/rundaverun-local/app/public"

declare -A posts=(
  [106]="/tmp/post106_styles_fixed.html"
  [107]="/tmp/post107_fixed.html"
  [109]="/tmp/post109_fixed.html"
  [151]="/tmp/post151_fixed.html"
  [245]="/tmp/post245_fixed.html"
  [249]="/tmp/post249_fixed.html"
  [328]="/tmp/post328_fixed.html"
  [699]="/tmp/post699_fixed.html"
  [700]="/tmp/post700_fixed.html"
  [716]="/tmp/post716_fixed.html"
  [717]="/tmp/post717_fixed.html"
  [934]="/tmp/post934_fixed.html"
  [941]="/tmp/post941_fixed.html"
  [942]="/tmp/post942_fixed.html"
)

for post_id in "${!posts[@]}"; do
  file="${posts[$post_id]}"
  echo "Restoring Post $post_id from $file..."
  wp post update "$post_id" --post_content="$(cat "$file")" --allow-root
  if [ $? -eq 0 ]; then
    echo "✓ Post $post_id restored successfully"
  else
    echo "✗ FAILED to restore Post $post_id"
  fi
done
```

---

## POST-RESTORATION VERIFICATION

After fixing, run these commands to verify:

```bash
# Check if any shell commands remain
wp db query "SELECT COUNT(*) as remaining FROM wp_7e1ce15f22_posts WHERE post_status='publish' AND post_content LIKE '%\$(cat%'" --allow-root

# Should return: remaining = 0

# Verify specific posts were updated
wp post get 106 --field=post_content --allow-root | head -c 100
wp post get 107 --field=post_content --allow-root | head -c 100
wp post get 699 --field=post_content --allow-root | head -c 100

# Check the website
curl -s http://rundaverun-local.local/about-dave | grep -c "\$(cat"
# Should return: 0
```

---

## ROOT CAUSE ANALYSIS

**What Went Wrong:**

1. **Initial Problem:** Content needed to be updated in WordPress
2. **Solution Attempted:** Content was saved to `/tmp/` files
3. **Implementation Error:** Instead of reading file contents and inserting HTML, the literal command syntax `$(cat /tmp/file.html)` was inserted into post_content
4. **Command Substitution Failed:** The shell command was never executed, so it displays as literal text
5. **Nested Commands:** Some fixes attempted to fix the problem but created more nested commands
6. **Result:** Public-facing pages show shell commands instead of content

**Why This Is Particularly Bad:**

- **Key Pages Affected:** About Dave, Our Plan, Contact - the most important pages
- **Professional Image:** Makes campaign appear unprofessional/broken
- **Security Exposure:** Shows internal file paths and development artifacts
- **User Trust:** Visitors see "backend code" which damages credibility
- **SEO Impact:** Search engines see shell commands instead of content

---

## PREVENTION RECOMMENDATIONS

To prevent this in the future:

1. **Never insert `$(command)` into database content**
   - Execute command first, capture output, then insert output

2. **Always use proper command substitution:**
   ```bash
   # WRONG - inserts literal command
   wp post update 123 --post_content='$(cat file.html)'

   # RIGHT - inserts file contents
   wp post update 123 --post_content="$(cat file.html)"
   ```

3. **Verify updates immediately:**
   ```bash
   wp post get 123 --field=post_content | head -c 100
   ```

4. **Use staging environment for bulk updates**

5. **Create rollback backups before bulk operations:**
   ```bash
   wp db export backup_$(date +%Y%m%d_%H%M%S).sql
   ```

---

## FILES TO PRESERVE

**DO NOT DELETE** these temp files until restoration is verified:

```
/tmp/post106_styles_fixed.html
/tmp/post107_fixed.html
/tmp/post109_fixed.html
/tmp/post151_fixed.html
/tmp/post245_fixed.html
/tmp/post249_fixed.html
/tmp/post328_fixed.html
/tmp/post699_fixed.html
/tmp/post700_fixed.html
/tmp/post716_fixed.html
/tmp/post717_fixed.html
/tmp/post934_fixed.html
/tmp/post941_fixed.html
/tmp/post942_fixed.html
```

**After successful restoration**, create a backup archive:

```bash
tar -czf /home/dave/skippy/conversations/wordpress_post_backups_2025-11-04.tar.gz \
  /tmp/post*_fixed.html \
  /tmp/post_*.html
```

---

## TIMELINE OF EVENTS (INFERRED)

Based on file timestamps and content:

1. **November 3, 01:02-01:22:** Initial batch of posts updated
   - Multiple `_fixed.html` files created
   - Some posts got shell commands instead of content

2. **November 3, 01:40-01:49:** First fix attempt
   - New "budget_fixed" files created
   - More nested commands introduced

3. **November 3, 04:35:** Second fix attempt
   - "real_fix" files created for posts 105 and 716
   - Still contained nested commands

4. **November 3, 21:56-22:47:** Additional backup files created
   - Multiple versions (_before, _fixed, _v2) for posts 138, 145, 148, 155, 184, 186, 244, 703, 940

**Current Status:** Problem persists in 14 posts as of November 4, 2025

---

## IMPACT ASSESSMENT

**Critical Pages Down:**
- About Dave (106) - Primary candidate bio page
- Our Plan (107) - Campaign platform overview
- Contact (109) - How to reach campaign

**Policy Documents Affected:**
- 9 detailed policy documents showing shell commands

**Estimated Visitor Impact:**
- Any visitor to these 14 pages sees broken content
- First impression: "This campaign's website is broken"
- Lost credibility and professionalism

**Priority for Fix:** IMMEDIATE - These are core campaign pages

---

## CONCLUSION

This is a critical content corruption issue affecting 14 published pages and policy documents. All affected posts display shell command syntax (`$(cat /tmp/file.html)`) instead of their intended HTML content.

**Good News:**
- All correct content exists in backup files
- No actual data loss occurred
- Fix is straightforward with WP-CLI
- No security breach, just display issue

**Action Required:**
- Execute the restoration commands above
- Verify all 14 posts display correctly
- Test on live site
- Archive backup files for safety

**Estimated Fix Time:** 5-10 minutes

---

**Report Generated:** November 4, 2025
**Scan Tool:** WP-CLI + Database queries
**Database:** local.wp_7e1ce15f22_posts
**Total Scan Time:** ~5 minutes
