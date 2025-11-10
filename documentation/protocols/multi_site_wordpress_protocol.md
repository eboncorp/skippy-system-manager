# Multi-Site WordPress Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

Managing both production (rundaverun) and local development (rundaverun-local) WordPress sites requires clear protocols for when to use each environment and how to sync changes.

## Purpose

- Prevent accidental production changes
- Enable safe testing and development
- Maintain sync between environments
- Ensure smooth deployments

---

## Sites Overview

| Environment | Name | Location | Purpose |
|-------------|------|----------|---------|
| **Production** | rundaverun | GoDaddy | Live campaign site |
| **Local Dev** | rundaverun-local | Local machine | Testing & development |

---

## When to Use Each Environment

### Use LOCAL (rundaverun-local) for:
- ✅ Testing new features
- ✅ Experimenting with changes
- ✅ Debugging issues
- ✅ Content drafting
- ✅ Plugin testing
- ✅ Any risky operations

### Use PRODUCTION (rundaverun) for:
- ⚠️ **ONLY** publishing approved content
- ⚠️ Critical hotfixes (with caution)
- ⚠️ Emergency corrections

### NEVER on Production:
- ❌ Experimental changes
- ❌ Unverified content
- ❌ Plugin testing
- ❌ Risky operations

---

## Standard Workflow

### Development → Production Flow

```bash
# 1. DEVELOP LOCALLY
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Make changes to local site
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 2. VERIFY LOCALLY
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after_local.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after_local.html"

# 3. TEST LOCALLY
# - View in browser
# - Test all links
# - Check mobile view
# - Run diagnostics

# 4. APPLY TO PRODUCTION (after approval)
SESSION_DIR_PROD="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_production_deployment"
mkdir -p "$SESSION_DIR_PROD"

# Backup production first
wp post get 105 --field=post_content > "$SESSION_DIR_PROD/page_105_before_prod.html"

# Apply same changes
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# Verify production
wp post get 105 --field=post_content > "$SESSION_DIR_PROD/page_105_after_prod.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR_PROD/page_105_after_prod.html"
```

---

## Environment-Specific Session Directories

```bash
# LOCAL work
/home/dave/skippy/work/wordpress/rundaverun-local/YYYYMMDD_HHMMSS_description/

# PRODUCTION work
/home/dave/skippy/work/wordpress/rundaverun/YYYYMMDD_HHMMSS_description/
```

**Always use correct path for environment!**

---

## Safety Checklist

Before making production changes:
- [ ] Tested on local first
- [ ] Verified changes work correctly
- [ ] Fact-checked all data
- [ ] Created production backup
- [ ] Have rollback plan ready
- [ ] User approved (if required)

---

## Quick Reference

```bash
# Check which site you're working on
wp option get siteurl

# Expected outputs:
# Local: http://rundaverun-local.local
# Production: https://rundaverun.com
```

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
