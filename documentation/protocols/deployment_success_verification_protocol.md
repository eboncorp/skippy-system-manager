# Deployment Success Verification Protocol

**Version:** 1.1.0
**Last Updated:** 2025-11-07
**Owner:** Claude Code / Dave

---

## Context

Formal criteria for when deployment is truly "done" and successful.

## Purpose

- Clear success criteria
- No ambiguity about completion
- Comprehensive verification
- Sign-off checklist

## Related Protocols

⚠️ **IMPORTANT:** This protocol should be used in conjunction with:
- `wordpress_site_diagnostic_protocol.md` - For comprehensive 7-layer diagnostics
- Use the WordPress Site Diagnostic Protocol for deep content and navigation validation

---

## Success Criteria Checklist

### Pre-Deployment
- [ ] All pre-deployment validations passed
- [ ] Zero broken links detected
- [ ] No false claims in content
- [ ] Security scan passed
- [ ] Database backup created
- [ ] Dry-run successful

### Deployment
- [ ] All files uploaded successfully
- [ ] No upload errors
- [ ] File permissions correct
- [ ] .env file configured
- [ ] Dependencies installed

### Post-Deployment
- [ ] Website accessible (HTTP 200)
- [ ] All plugins active and healthy
- [ ] No PHP errors in logs
- [ ] Database connection successful
- [ ] Cron jobs configured
- [ ] **Run 7-Layer Diagnostic** (see `wordpress_site_diagnostic_protocol.md`)
  - [ ] Layer 3: Content integrity verified (no bash commands in pages)
  - [ ] Layer 4: Navigation tested (all critical pages return 200)
  - [ ] Layer 6: Frontend rendering validated

### Feature Verification
- [ ] Analytics tracking verified (GA4)
- [ ] Email system tested (send/receive)
- [ ] PDF generation tested
- [ ] Forms tested (contact, volunteer)
- [ ] Policy pages accessible
- [ ] Budget page accurate

### Performance
- [ ] Page load < 3 seconds
- [ ] Mobile responsive
- [ ] No console errors
- [ ] Images load correctly

### Security
- [ ] HTTPS working
- [ ] Security headers present
- [ ] No sensitive data exposed
- [ ] File permissions secure

---

## Automated Verification

```bash
# Run all verification scripts
bash ~/rundaverun/campaign/skippy-scripts/wordpress/deployment_verification_v1.0.0.sh
bash ~/rundaverun/campaign/skippy-scripts/wordpress/wordpress_health_check_v1.0.0.sh
```

---

## Manual Verification

**User Must Check:**
1. Visit website in browser
2. Test all forms
3. Verify content accuracy
4. Check mobile view
5. Test PDF downloads

---

## Sign-Off

**Deployment Successful When:**
- ✅ All automated checks pass
- ✅ Manual verification complete
- ✅ No critical errors
- ✅ Performance acceptable
- ✅ User sign-off given

---

## Quick Verification Commands

```bash
# Website accessible
curl -I https://rundaverun.org | grep "200 OK"

# WordPress health
wp health-check

# Check for PHP errors
tail -f ~/html/wp-content/debug.log | grep "ERROR"

# Test email
wp eval "wp_mail('test@example.com', 'Test', 'Testing');"

# Performance test
curl -w "@curl-format.txt" -o /dev/null -s https://rundaverun.org
```

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
