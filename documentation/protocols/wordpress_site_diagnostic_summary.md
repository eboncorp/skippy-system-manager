# WordPress Site Diagnostic Protocol - Quick Summary

**Protocol File:** `wordpress_site_diagnostic_protocol.md`
**Script:** `/home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.0.0.sh`
**Created:** 2025-11-07

---

## What This Addresses

On 2025-11-07, user reported "the site has problems" but initial diagnostic showed:
- ✅ HTTP 200 response
- ✅ No PHP errors
- ✅ Plugins active
- ✅ Database tables exist

**However, screenshots revealed:**
- ❌ Pages displayed bash command strings: `$(cat /path/to/file.html)`
- ❌ Policy pages returned 404 errors
- ❌ Navigation was broken

**Root cause:** Initial diagnostic only checked infrastructure, not actual content/UX.

---

## The 7-Layer Diagnostic Model

### Layer 1: Infrastructure Health ⚙️
- HTTP response codes
- PHP/WordPress versions
- Database connectivity
- Disk space

### Layer 2: Plugin & Theme Health 🔌
- Plugin activation status
- Plugin errors
- Database tables exist
- Theme active

### Layer 3: Content Integrity 📝 **← NEW**
- Check for bash commands in content
- Check for PHP code in pages
- Verify critical pages have content
- No HTML encoding issues

### Layer 4: Navigation & URL Structure 🗺️ **← NEW**
- Test critical page URLs
- Test policy document URLs
- Verify rewrite rules exist
- Check for 404 errors

### Layer 5: Database Content Validation 🗄️ **← NEW**
- Verify post counts
- Check for orphaned content
- Check for duplicate slugs
- Menu structure intact

### Layer 6: Frontend Rendering 🎨 **← NEW**
- CSS/JS assets present
- Page renders with content
- Shortcodes render properly
- No white screen of death

### Layer 7: User Experience Testing 👤 **← NEW**
- Screenshot verification
- Form submission tests
- Mobile responsiveness
- Navigation functionality

---

## Quick Commands

###60-Second Health Check:
```bash
# Infrastructure
curl -I http://site.local | head -1

# Content integrity
wp db query "SELECT COUNT(*) FROM wp_posts WHERE post_content LIKE '%\$(cat%'"

# Navigation
curl -s -o /dev/null -w "%{http_code}" http://site.local/our-plan/

# Database
wp post list --post_type=page --format=count
```

### 5-Minute Diagnostic:
```bash
cd "/path/to/wordpress"

# Layer 1-2: Infrastructure & Plugins
wp cli info
wp plugin list --status=active,error

# Layer 3: Content Integrity
wp db query "SELECT ID, post_title FROM wp_posts WHERE post_type='page' AND (post_content LIKE '%\$(cat%' OR post_content LIKE '%<?php%')"

# Layer 4: Navigation
for url in / /our-plan /voter-education; do
    echo -n "$url: "
    curl -s -o /dev/null -w "%{http_code}" "http://site.local$url"
    echo ""
done

# Layer 5: Database
echo "Pages: $(wp post list --post_type=page --format=count)"
echo "Orphaned: $(wp db query 'SELECT COUNT(*) FROM wp_posts WHERE post_parent NOT IN (SELECT ID FROM wp_posts) AND post_parent != 0' | tail -1)"

# Layer 6: Frontend
curl -s http://site.local | wc -w
```

---

## Red Flags

**Content Issues:**
- `$(cat ...)` in post_content
- `<?php ...` in post_content
- Critical pages < 100 characters
- Suspicious JavaScript patterns

**Navigation Issues:**
- Critical pages return 404
- Zero rewrite rules
- Broken menu links

**Database Issues:**
- Missing plugin tables
- Orphaned content
- Duplicate slugs

**Rendering Issues:**
- Page word count < 50
- Missing CSS/JS files
- Shortcodes displaying as text

---

## When to Use

**Always use after:**
- Deployments
- Plugin activation/merge
- User reports "site has problems"
- WordPress/PHP updates

**Weekly maintenance:**
- Quick 60-second check

**Monthly:**
- Full 7-layer diagnostic

---

## Integration

**Extends:**
- `deployment_success_verification_protocol.md` (now references Layer 3-7)

**Required before:**
- Declaring site "healthy"
- Signing off on deployment
- Closing bug tickets

---

## Case Study: rundaverun-local (2025-11-07)

**Problem:** User said "site has problems" but initial scan showed healthy.

**Traditional Diagnostic (insufficient):**
```
✅ HTTP 200
✅ No PHP errors
✅ Plugins active
✅ DB tables exist
❌ MISSED: Content corruption
❌ MISSED: Navigation broken
```

**7-Layer Diagnostic (comprehensive):**
```
✅ Layer 1: Infrastructure - OK
✅ Layer 2: Plugins - OK
❌ Layer 3: Pages 107, 337 have bash commands
❌ Layer 4: Policy pages return 404
✅ Layer 5: Database - OK
❌ Layer 6: Pages render command strings
❌ Layer 7: Screenshots show broken UX
```

**Resolution:** Fixed in 10 minutes after Layer 3 & 4 checks revealed the issues.

---

## Files Created

1. `/home/dave/skippy/documentation/protocols/wordpress_site_diagnostic_protocol.md` - Full protocol (15KB)
2. `/home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.0.0.sh` - Automated script
3. `/home/dave/skippy/conversations/rundaverun_local_site_diagnostic_2025-11-07.md` - Case study
4. This summary document

---

**Status:** ✅ Active
**Version:** 1.0.0
**Last Updated:** 2025-11-07
