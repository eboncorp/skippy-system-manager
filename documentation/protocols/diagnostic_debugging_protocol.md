# Diagnostic & Debugging Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

When issues arise with WordPress sites, scripts, or systems, follow a systematic diagnostic approach to identify and resolve problems efficiently.

## Purpose

- Quickly identify root causes of issues
- Minimize downtime and disruption
- Document findings for future reference
- Prevent issue recurrence

---

## When to Use This Protocol

**Use for:**
- ✅ WordPress site errors or issues
- ✅ Script failures or unexpected behavior
- ✅ Performance problems
- ✅ Content display issues
- ✅ Broken links or missing content

**Don't use for:**
- ❌ Planned updates (use update protocols)
- ❌ New feature development
- ❌ Routine maintenance

---

## Diagnostic Tools Available

### WordPress Diagnostics
```bash
# Comprehensive diagnostic (10 layers)
bash /home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.3.0.sh

# Quick health check
wp eval 'wp_get_update_php_url(); echo current_theme();'

# Check for errors
wp eval 'error_get_last();'
```

###Content Verification
```bash
# Check for empty pages
wp post list --post_type=page --fields=ID,post_title --format=csv | \
  while IFS=, read id title; do
    length=$(wp post get $id --field=post_content | wc -c)
    if [ $length -lt 10 ]; then echo "$id: $title (EMPTY - $length chars)"; fi
  done

# Check for broken links
grep -r "href=\"/policy/\"" # Should be /policies/
```

---

## Diagnostic Workflow

### Phase 1: Initial Assessment

1. **Document the issue:**
   ```bash
   SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_debug_{issue}"
   mkdir -p "$SESSION_DIR"

   cat > "$SESSION_DIR/ISSUE_DESCRIPTION.md" <<EOF
   # Issue Description
   **Reported:** $(date)
   **Reporter:** [User/System]
   **Severity:** [Critical/High/Medium/Low]

   ## Symptoms
   - [What's wrong]
   - [Expected vs actual behavior]

   ## Steps to Reproduce
   1. [Step 1]
   2. [Step 2]
   EOF
   ```

2. **Run comprehensive diagnostic:**
   ```bash
   bash /home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.3.0.sh > "$SESSION_DIR/diagnostic_output.txt"
   ```

3. **Review diagnostic output:**
   ```bash
   grep -E "ERROR|WARNING|FAIL" "$SESSION_DIR/diagnostic_output.txt"
   ```

### Phase 2: Investigation

4. **Check logs:**
   ```bash
   # WordPress debug log
   tail -50 /path/to/wordpress/wp-content/debug.log

   # PHP error log
   sudo tail -50 /var/log/apache2/error.log
   ```

5. **Test specific functionality:**
   ```bash
   # Test specific page
   wp post get {ID} --field=post_status

   # Test plugins
   wp plugin list --status=active
   ```

### Phase 3: Resolution

6. **Apply fix based on findings**
7. **Verify fix worked**
8. **Document resolution**

---

## Common Issues & Solutions

### Issue: Empty Pages

**Symptoms:** Page exists but shows no content
**Diagnostic:**
```bash
wp post get {ID} --field=post_content | wc -c  # Shows 0 or very small number
```

**Solution:**
```bash
# Restore from backup or markdown source
# Follow WordPress Content Update Protocol
```

### Issue: Broken Internal Links

**Symptoms:** Links return 404
**Diagnostic:**
```bash
grep -r "href=\"/policy/\"" # Wrong path
```

**Solution:**
```bash
wp search-replace 'href="/policy/' 'href="/policies/'
```

### Issue: Plugin Conflicts

**Symptoms:** Content disappears after update
**Diagnostic:**
```bash
# Try update with plugins skipped
wp post update {ID} --post_content="test" --skip-plugins
```

**Solution:**
```bash
# Identify conflicting plugin and disable/update
```

---

## Debugging Checklist

- [ ] Created debug session directory
- [ ] Documented issue description
- [ ] Ran diagnostic script
- [ ] Reviewed error logs
- [ ] Identified root cause
- [ ] Applied fix
- [ ] Verified fix works
- [ ] Documented resolution

---

## Related Protocols

- [Verification Protocol](verification_protocol.md)
- [WordPress Content Update Protocol](wordpress_content_update_protocol.md)
- [Error Recovery Protocol](error_recovery_protocol.md)

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
