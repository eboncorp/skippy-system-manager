# Live Site Upgrade Checklist - rundaverun.org
**Date:** November 1, 2025
**Current Status:** Proofreading fixes deployed, glossary features missing

---

## ✅ Already Deployed to Live Site

### Proofreading Fixes (Completed Nov 1, 2025)
- [x] Policy 355 (Economic Development) - Fixed triple apostrophes
- [x] Policy 356 (Health & Human Services) - Fixed triple apostrophes
- [x] Policy 245 (About Dave) - Removed "raised a family", updated "46 substations"
- [x] Page 337 (Voter Education) - Updated "46 substations", removed labels
- [x] Cache cleared

**Result:** Live site has clean, corrected content for all policy documents.

---

## ❌ Still Missing from Live Site

### 1. Voter Education Glossary Plugin
**Status:** Not installed on live site
**What it provides:**
- Custom post type for glossary terms
- Glossary archive page at `/glossary/`
- Single term pages with detailed explanations
- Category filtering and alphabetical navigation
- Search functionality

**Files needed:**
- `/tmp/claude_upload_20251101_225808/voter-education-glossary-plugin/`
- Located in: `claude_upload_complete_local_site_20251101.zip`

**Installation steps:**
1. Copy plugin folder to live site: `/html/wp-content/plugins/voter-education-glossary/`
2. Activate plugin via WP-CLI:
   ```bash
   ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com "cd /html && wp plugin activate voter-education-glossary"
   ```
3. Verify activation:
   ```bash
   ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com "cd /html && wp plugin list | grep glossary"
   ```

---

### 2. 351 Glossary Terms
**Status:** Zero glossary terms on live site
**What's missing:**
- 351 comprehensive glossary terms
- Covering Louisville Metro government, budget, civic engagement
- Each with definition, Louisville context, "why it matters"
- Organized in 13 categories

**Data location:**
- Database export: `rundaverun_local_complete_20251101.sql`
- JSON file: `voter-education-glossary-plugin/glossary_complete_final.json`

**Import options:**

**Option A: Full database import (fastest but risky)**
```bash
# Backup live database first!
ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com "cd /html && wp db export backup_before_glossary_import.sql"

# Import just glossary tables (safer)
# Extract only glossary-related tables from local SQL
# Import those specific tables
```

**Option B: JSON import via plugin (recommended)**
```bash
# Upload JSON file
scp voter-education-glossary-plugin/glossary_complete_final.json \
    git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com:/html/wp-content/uploads/

# Import via WP-CLI (requires custom script)
# OR import via WordPress admin: Glossary → Import Terms
```

**Option C: Manual WordPress export/import**
1. On local site: Export glossary terms via WordPress Tools → Export
2. Upload XML file to live site
3. Import via WordPress Tools → Import

---

### 3. Navigation Menu "Glossary" Link
**Status:** Menu exists but no Glossary link
**What's needed:**
- Add "Glossary" link to main navigation menu
- Points to: `/glossary/` or `/voter-education-glossary/`
- Position: Between "Policy Library" and "Get Involved"

**Current menu (8 items):**
1. Home
2. About Dave
3. Our Plan
4. Voter Education
5. Policy Library
6. ~~Glossary~~ ← MISSING
7. Get Involved
8. Contact

**Add via WP-CLI:**
```bash
# Find glossary archive page ID
ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com "cd /html && wp post list --post_type=page --s='glossary' --fields=ID,post_title"

# Add to menu (menu ID 35, position 6)
ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com "cd /html && wp menu item add-post 35 [PAGE_ID] --title='Glossary' --position=6"
```

---

### 4. Voter Education Page Link
**Status:** Page exists but needs glossary link updated
**What's needed:**
- Update "Explore Glossary →" button to point to correct glossary URL
- Verify glossary shortcode works: `[featured_glossary_terms]`

**Verification:**
```bash
ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com "cd /html && wp post get 337 --field=post_content | grep -i glossary"
```

---

## 🎯 Recommended Deployment Order

### Phase 1: Plugin Installation (5 minutes)
1. Upload voter-education-glossary plugin
2. Activate plugin
3. Verify plugin is active
4. Check for errors in plugin activation

### Phase 2: Import Glossary Terms (10-15 minutes)
1. Backup live database first
2. Upload JSON import file
3. Import 351 terms via plugin importer
4. Verify term count: `wp post list --post_type=glossary_term --format=count`
5. Check a few sample terms

### Phase 3: Navigation & Testing (5 minutes)
1. Add "Glossary" link to navigation menu
2. Clear all caches
3. Test glossary archive page: https://rundaverun.org/glossary/
4. Test term search and filtering
5. Test category navigation

**Total estimated time:** 20-25 minutes

---

## 📋 Verification Checklist

After deployment, verify:

- [ ] Plugin shows in active plugins list
- [ ] `wp post list --post_type=glossary_term --format=count` returns 351
- [ ] Glossary archive accessible at `/glossary/`
- [ ] Alphabetical filter works (A-Z links)
- [ ] Category filter works
- [ ] Search functionality works
- [ ] Individual term pages load correctly
- [ ] Navigation menu shows "Glossary" link
- [ ] "Featured Terms" section displays on Voter Education page
- [ ] No PHP errors in error log

---

## 🚨 Rollback Plan (If Needed)

If anything goes wrong:

1. **Deactivate plugin:**
   ```bash
   wp plugin deactivate voter-education-glossary
   ```

2. **Restore database backup:**
   ```bash
   wp db import backup_before_glossary_import.sql
   ```

3. **Remove menu item:**
   ```bash
   wp menu item delete [ITEM_ID]
   ```

4. **Clear cache and verify site works**

---

## 📁 File Locations

**On local machine:**
- Plugin: `/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/voter-education-glossary/`
- Database: `/tmp/claude_upload_20251101_225808/rundaverun_local_complete_20251101.sql`
- Zip package: `/tmp/claude_upload_complete_local_site_20251101.zip`

**Upload package includes:**
- Complete plugin code
- JSON import file with 351 terms
- Database export with all data
- Installation instructions

---

## 🎯 Expected End State

After completing all upgrades, live site will have:

✅ All proofreading fixes (already done)
✅ Voter education glossary plugin installed
✅ 351 glossary terms accessible
✅ Glossary archive page at `/glossary/`
✅ Navigation menu with Glossary link
✅ Featured glossary terms on Voter Education page
✅ Fully functional search and filtering

**Result:** Live site matches local site exactly.

---

## 🤔 Questions Before Starting?

1. **Do you want to backup the live database first?** (Recommended: Yes)
2. **Preferred import method?** (Recommended: JSON via plugin)
3. **Test on staging first?** (If available)
4. **Deploy during low-traffic time?** (Recommended: Yes)

---

**Next Action:** Upload plugin and import glossary terms to complete the live site upgrade.

**Estimated Downtime:** None (all changes are additive)
**Risk Level:** Low (only adding new features, not modifying existing content)
