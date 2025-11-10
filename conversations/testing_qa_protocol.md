# Testing & QA Protocol

**Date Created**: 2025-10-28
**Purpose**: Standardized testing and quality assurance procedures
**Applies To**: All code changes, deployments, and releases
**Priority**: HIGH (prevents bugs, ensures quality)

## Purpose

This protocol establishes:
- Testing workflows at all levels (unit, integration, system, UAT)
- WordPress-specific local and production testing procedures
- Browser and mobile device testing requirements
- Performance benchmarking standards
- Regression testing to prevent breaking existing functionality

---

## Overview

This protocol establishes testing standards to ensure all changes are properly validated before deployment. Systematic testing prevents bugs from reaching production and ensures a stable, reliable user experience.

## Core Testing Principles

### 1. Test Before Deploy
✅ **ALWAYS** test locally before production deployment
✅ **NEVER** deploy directly to production without testing
✅ Test in an environment that mirrors production

### 2. Test Systematically
✅ Follow a checklist (don't rely on memory)
✅ Test one change at a time
✅ Document test results
❌ Don't skip steps
❌ Don't assume "it should work"

### 3. Test the User Experience
✅ Test as an end user would use it
✅ Test on multiple browsers and devices
✅ Test edge cases and error conditions
❌ Don't just test the "happy path"

### 4. Regression Testing
✅ Test that old features still work
✅ Verify no unintended side effects
✅ Check that bug fixes don't break other things

---

## Testing Levels

### Level 1: Unit Testing (Code Level)
**What**: Testing individual functions/components
**When**: During development
**Who**: Developer

### Level 2: Integration Testing
**What**: Testing how components work together
**When**: After unit testing passes
**Who**: Developer

### Level 3: System Testing
**What**: Testing the complete system
**When**: Before deployment
**Who**: Developer/QA

### Level 4: User Acceptance Testing
**What**: Testing from user perspective
**When**: Before production release
**Who**: End user or stakeholder

---

## WordPress Testing Protocol

### Local Testing Workflow

#### 1. Development Environment Setup

```bash
# Verify local environment matches production
# WordPress version
wp core version --allow-root

# PHP version
php -v

# Active plugins
wp plugin list --status=active --allow-root

# Active theme
wp theme list --status=active --allow-root
```

**Checklist**:
- [ ] WordPress version matches production
- [ ] PHP version compatible
- [ ] Same plugins activated
- [ ] Same theme activated
- [ ] Database has representative data

#### 2. Pre-Test Baseline

**Create clean baseline**:
```bash
# Backup current state
DATE=$(date +%Y%m%d_%H%M%S)
wp db export "/home/dave/rundaverun/backups/pre_test_${DATE}.sql" --allow-root

# Document current state
wp plugin list --allow-root > "pre_test_plugins_${DATE}.txt"
wp theme list --allow-root > "pre_test_themes_${DATE}.txt"
```

- [ ] Baseline backup created
- [ ] Current state documented
- [ ] Ready to make changes

#### 3. Make Changes

- [ ] Changes made to local environment
- [ ] Changes documented
- [ ] Git commit created (if using git)

#### 4. Functional Testing

**Test changed functionality**:
- [ ] New feature works as expected
- [ ] Changed feature works as expected
- [ ] No errors in WordPress debug log
- [ ] No JavaScript errors in browser console
- [ ] No PHP errors displayed

**Test affected areas**:
- [ ] Related features still work
- [ ] Dependent functionality unchanged
- [ ] Data integrity maintained

**Example**: If you changed the glossary:
```bash
# Test glossary functionality
# Open http://rundaverun-local.local/glossary in browser

# Check:
- [ ] Glossary page loads
- [ ] Search functionality works
- [ ] All terms display correctly
- [ ] Links work
- [ ] Mobile layout works
- [ ] No JavaScript errors (F12 console)
```

#### 5. Browser Testing

**Desktop Browsers**:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (if available)
- [ ] Edge (if available)

**For each browser**:
- [ ] Page loads correctly
- [ ] No layout issues
- [ ] Interactive elements work
- [ ] No console errors

**Mobile Browsers**:
- [ ] Chrome Mobile (DevTools simulation)
- [ ] Safari Mobile (DevTools simulation)
- [ ] Actual mobile device (if possible)

**For each mobile browser**:
- [ ] Mobile layout correct
- [ ] Mobile menu works
- [ ] Touch interactions work
- [ ] No horizontal scrolling
- [ ] Text readable (minimum 16px)

#### 6. Performance Testing

```bash
# Check page load time
# Use browser DevTools Network tab

# Check database query count
wp db query "SHOW PROCESSLIST" --allow-root

# Check for slow queries
# Enable WordPress debug logging:
# In wp-config.php: define('SAVEQUERIES', true);
```

- [ ] Page load time < 3 seconds
- [ ] No excessive database queries
- [ ] Images optimized
- [ ] No memory issues
- [ ] No performance degradation

#### 7. Accessibility Testing

- [ ] Images have alt text
- [ ] Headings properly nested (H1 → H2 → H3)
- [ ] Links descriptive
- [ ] Color contrast sufficient
- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Screen reader friendly (if possible to test)

#### 8. Content Validation

- [ ] All text displays correctly
- [ ] No placeholder text (Lorem ipsum)
- [ ] No debug output visible
- [ ] Spelling and grammar correct
- [ ] Links work (no 404s)
- [ ] Images display correctly

#### 9. Security Testing

- [ ] No credentials in code
- [ ] No sensitive data exposed
- [ ] SQL injection prevented
- [ ] XSS (Cross-Site Scripting) prevented
- [ ] CSRF tokens used (for forms)
- [ ] File uploads restricted (if applicable)

---

## Script Testing Protocol

### Before Testing

```bash
# Syntax check
bash -n script_name.sh

# For Python
python3 -m py_compile script_name.py
```

### Test Environments

1. **Development**: Local machine, test data
2. **Staging**: Copy of production, production-like data
3. **Production**: Live environment

**ALWAYS test in development first, then staging, then production**

### Script Testing Checklist

#### Functionality Testing
- [ ] Script runs without errors
- [ ] Produces expected output
- [ ] Handles valid input correctly
- [ ] Handles invalid input gracefully

#### Error Handling Testing
```bash
# Test with missing arguments
./script.sh

# Test with invalid arguments
./script.sh --invalid-option

# Test with non-existent files
./script.sh --input nonexistent.txt

# Test with insufficient permissions
chmod 000 test_file.txt
./script.sh --input test_file.txt
```

- [ ] Missing arguments handled
- [ ] Invalid arguments handled
- [ ] File not found handled
- [ ] Permission denied handled
- [ ] Network failures handled (if applicable)

#### Edge Cases
- [ ] Empty input
- [ ] Very large input
- [ ] Special characters in input
- [ ] Whitespace in filenames
- [ ] Multiple simultaneous runs (race conditions)

#### Exit Codes
```bash
# Test exit codes
./script.sh --input valid.txt
echo $?  # Should be 0

./script.sh --input invalid.txt
echo $?  # Should be non-zero
```

- [ ] Success returns 0
- [ ] Errors return non-zero
- [ ] Different errors return different codes

#### Dependencies
```bash
# Test with missing dependencies
# Temporarily rename dependency to test error handling
```

- [ ] Missing dependencies detected
- [ ] Clear error message shown
- [ ] Graceful failure

#### Cleanup Testing
- [ ] Temporary files removed
- [ ] Resources released
- [ ] No leftover processes
- [ ] No corrupted state on failure

---

## Deployment Testing Protocol

Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`

### Pre-Deployment Testing

**Complete checklist from deployment protocol**:
- [ ] All local tests pass
- [ ] Browser testing complete
- [ ] Mobile testing complete
- [ ] Performance acceptable
- [ ] Backup created

### Post-Deployment Testing

**Critical Path Testing** (within 5 minutes of deployment):
```bash
# Homepage
curl -I https://rundaverun.org
# Should return: HTTP/2 200

# Key pages
curl -I https://rundaverun.org/policy
curl -I https://rundaverun.org/glossary
curl -I https://rundaverun.org/contact
```

- [ ] Homepage loads (200 OK)
- [ ] Critical pages load
- [ ] No 500 errors
- [ ] No database errors
- [ ] SSL certificate valid

**Functional Testing** (within 15 minutes):
- [ ] Login works (if applicable)
- [ ] Forms submit correctly
- [ ] Search works (if applicable)
- [ ] Navigation menus work
- [ ] Mobile menu works

**Content Verification** (within 30 minutes):
- [ ] New content visible
- [ ] Changed content updated
- [ ] Images display
- [ ] Links work
- [ ] No broken references

**Monitoring** (first 24 hours):
- [ ] Check error logs regularly
- [ ] Monitor traffic (if analytics available)
- [ ] Watch for user reports
- [ ] Check server performance

---

## Regression Testing

**What**: Testing that old features still work after changes
**When**: After any code changes
**Why**: Prevent breaking existing functionality

### Regression Test Suite

**Core Functionality** (test every deployment):
- [ ] Homepage loads
- [ ] All main menu items work
- [ ] Contact form submits
- [ ] Search works (if applicable)
- [ ] User login/registration works (if applicable)

**WordPress Specific**:
- [ ] Admin panel accessible
- [ ] Can create/edit posts
- [ ] Can upload media
- [ ] Plugins still active
- [ ] Theme displays correctly

**Custom Features**:
- [ ] Glossary search works
- [ ] Policy documents load
- [ ] Mobile menu injector works
- [ ] Any custom shortcodes work

### Creating Regression Test Checklist

**After fixing a bug**:
1. Add test for the bug to regression suite
2. Verify fix works
3. Add to checklist for future deployments

**Example**:
```markdown
## Regression Test: Mobile Menu Bug (Fixed 2025-10-15)

**Bug**: Mobile menu didn't open on iOS Safari
**Fix**: Changed z-index from 999 to 9999
**Test**:
- [ ] Open site on iOS Safari
- [ ] Tap menu button
- [ ] Verify menu opens
- [ ] Verify menu items clickable
```

---

## Test Documentation

### Test Plan Template

```markdown
# Test Plan: [Feature/Change Name]

**Date**: 2025-10-28
**Version**: 1.0
**Tester**: [Name]

## Test Objective

What are we testing and why?

## Test Scope

### In Scope
- What will be tested

### Out of Scope
- What will NOT be tested

## Test Environment

- **Environment**: Local / Staging / Production
- **WordPress Version**: X.X.X
- **PHP Version**: X.X
- **Browser**: Chrome XX, Firefox XX, etc.
- **Device**: Desktop / Mobile / Tablet

## Test Cases

### TC-001: [Test Case Name]

**Objective**: What this test verifies

**Prerequisites**:
- Condition 1
- Condition 2

**Steps**:
1. Step 1
2. Step 2
3. Step 3

**Expected Result**:
What should happen

**Actual Result**:
What actually happened

**Status**: ✅ Pass / ❌ Fail

**Notes**:
Any observations

### TC-002: [Next Test Case]

[Same structure]

## Test Results Summary

- Total Test Cases: 10
- Passed: 9
- Failed: 1
- Blocked: 0

## Issues Found

### Issue 1: [Description]
**Severity**: Critical / High / Medium / Low
**Steps to Reproduce**: ...
**Expected**: ...
**Actual**: ...
**Status**: Open / Fixed / Won't Fix

## Recommendations

What should be done based on test results?

## Sign-Off

- [ ] All critical tests passed
- [ ] All high-priority tests passed
- [ ] Known issues documented
- [ ] Ready for deployment: Yes / No
```

### Test Results Log

```markdown
# Test Results: [Date]

**Test Date**: 2025-10-28
**Tested By**: Claude Code
**Version Tested**: 1.2.0
**Environment**: Local

## Summary

✅ Passed: 25
❌ Failed: 2
⚠️ Blocked: 1
Total: 28

Pass Rate: 89%

## Failed Tests

### Test: Mobile Menu on iOS
**Status**: ❌ Failed
**Issue**: Menu button not visible
**Action**: Bug report created

### Test: Search with Special Characters
**Status**: ❌ Failed
**Issue**: Search fails with quotes in query
**Action**: Bug report created

## Blocked Tests

### Test: Payment Gateway Integration
**Status**: ⚠️ Blocked
**Reason**: Test credentials not available
**Action**: Request credentials from team

## Passed Tests

- Homepage loads: ✅
- Navigation works: ✅
- Contact form: ✅
[... 22 more passed tests]

## Overall Assessment

**Ready for deployment?**: No (2 failed tests)
**Recommendation**: Fix mobile menu bug before deploying
```

---

## Automated Testing

### Shell Script Testing

**Create test script**:
```bash
#!/bin/bash
################################################################################
# test_backup_script.sh
# Automated tests for backup_wordpress.sh
################################################################################

# Test configuration
SCRIPT_TO_TEST="./backup_wordpress.sh"
TEST_DIR="/tmp/test_backup_$$"
PASS_COUNT=0
FAIL_COUNT=0

# Setup
setup_test_env() {
    mkdir -p "$TEST_DIR"
    # Create test data
}

# Cleanup
cleanup_test_env() {
    rm -rf "$TEST_DIR"
}

# Test functions
test_missing_arguments() {
    echo "TEST: Missing arguments..."
    $SCRIPT_TO_TEST 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "  ✅ PASS: Script correctly rejects missing arguments"
        ((PASS_COUNT++))
    else
        echo "  ❌ FAIL: Script should reject missing arguments"
        ((FAIL_COUNT++))
    fi
}

test_valid_backup() {
    echo "TEST: Valid backup creation..."
    $SCRIPT_TO_TEST --database test_db --output "$TEST_DIR/backup.sql"
    if [ -f "$TEST_DIR/backup.sql" ]; then
        echo "  ✅ PASS: Backup file created"
        ((PASS_COUNT++))
    else
        echo "  ❌ FAIL: Backup file not created"
        ((FAIL_COUNT++))
    fi
}

# Run tests
main() {
    echo "===== Running Tests ====="
    setup_test_env

    test_missing_arguments
    test_valid_backup
    # Add more tests...

    cleanup_test_env

    echo "===== Test Results ====="
    echo "Passed: $PASS_COUNT"
    echo "Failed: $FAIL_COUNT"

    if [ $FAIL_COUNT -eq 0 ]; then
        echo "✅ All tests passed!"
        exit 0
    else
        echo "❌ Some tests failed"
        exit 1
    fi
}

main
```

### WordPress Testing

**Use WP-CLI for automated tests**:
```bash
#!/bin/bash
# test_wordpress_site.sh
# Automated WordPress site tests

cd "/home/dave/Local Sites/rundaverun-local/app/public"

echo "===== WordPress Tests ====="

# Test 1: Database connection
echo "TEST: Database connection..."
if wp db check --allow-root &>/dev/null; then
    echo "  ✅ PASS: Database connection works"
else
    echo "  ❌ FAIL: Database connection failed"
fi

# Test 2: Core files
echo "TEST: WordPress core files..."
if wp core verify-checksums --allow-root &>/dev/null; then
    echo "  ✅ PASS: Core files intact"
else
    echo "  ❌ FAIL: Core files corrupted"
fi

# Test 3: Plugin status
echo "TEST: Plugin status..."
BROKEN_PLUGINS=$(wp plugin list --status=inactive --format=count --allow-root)
if [ "$BROKEN_PLUGINS" -eq 0 ]; then
    echo "  ✅ PASS: No broken plugins"
else
    echo "  ⚠️  WARNING: $BROKEN_PLUGINS inactive plugins"
fi

# Test 4: Homepage accessibility
echo "TEST: Homepage loads..."
if curl -s -o /dev/null -w "%{http_code}" http://rundaverun-local.local | grep -q "200"; then
    echo "  ✅ PASS: Homepage loads (200 OK)"
else
    echo "  ❌ FAIL: Homepage not accessible"
fi

echo "===== Tests Complete ====="
```

---

## Quality Assurance Checklist

### Pre-Release QA

**Code Quality**:
- [ ] No debug code (console.log, var_dump, etc.)
- [ ] No TODO/FIXME in production code
- [ ] No commented-out code blocks
- [ ] No hardcoded credentials
- [ ] Error handling implemented
- [ ] Input validation implemented

**Functionality**:
- [ ] All features work as specified
- [ ] Edge cases handled
- [ ] Error messages clear and helpful
- [ ] User feedback provided (loading states, success messages)

**Performance**:
- [ ] Page load time acceptable (< 3 seconds)
- [ ] No memory leaks
- [ ] Database queries optimized
- [ ] Images optimized
- [ ] Caching implemented where appropriate

**Security**:
- [ ] Input sanitized
- [ ] Output escaped
- [ ] SQL injection prevented
- [ ] XSS prevented
- [ ] CSRF tokens used
- [ ] Authentication/authorization correct

**Compatibility**:
- [ ] Works on target browsers
- [ ] Works on mobile devices
- [ ] Works on different screen sizes
- [ ] Backwards compatible (if applicable)

**Documentation**:
- [ ] Code documented
- [ ] User documentation updated
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] Version number incremented

**Testing**:
- [ ] Unit tests pass (if applicable)
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Regression tests pass
- [ ] Performance testing done

---

## Testing Tools Reference

### Browser DevTools

**Console Tab**:
- View JavaScript errors
- Run JavaScript commands
- Debug JavaScript code

**Network Tab**:
- View all HTTP requests
- Check response codes
- View request/response headers
- Monitor load times

**Elements Tab**:
- Inspect HTML
- Modify CSS live
- Check responsive design

**Lighthouse** (in DevTools):
- Performance auditing
- Accessibility testing
- SEO analysis
- Best practices check

### WordPress Testing Tools

**WP-CLI**:
```bash
# Database check
wp db check --allow-root

# Verify core files
wp core verify-checksums --allow-root

# Check plugin status
wp plugin list --allow-root

# Search-replace verification
wp search-replace --dry-run 'old' 'new' --allow-root
```

**Query Monitor Plugin**:
- Database query debugging
- HTTP request monitoring
- PHP error tracking
- Performance profiling

### Command Line Tools

**curl**: HTTP testing
```bash
# Check response code
curl -I https://rundaverun.org

# Check response time
curl -w "@curl-format.txt" -o /dev/null -s https://rundaverun.org
```

**ab (Apache Bench)**: Load testing
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 https://rundaverun.org/
```

**shellcheck**: Shell script linting
```bash
shellcheck script.sh
```

---

## Integration with Other Protocols

### With Deployment Checklist Protocol
Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`
- Testing is part of deployment process
- Pre-deployment testing required
- Post-deployment verification required

### With Debugging Workflow Protocol
Reference: `/home/dave/skippy/conversations/debugging_workflow_protocol.md`
- When tests fail, use debugging workflow
- Document test failures
- Create regression tests for bugs

### With WordPress Maintenance Protocol
Reference: `/home/dave/skippy/conversations/wordpress_maintenance_protocol.md`
- WordPress-specific testing procedures
- WP-CLI testing commands
- GoDaddy deployment testing

### With Error Logging Protocol
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Log test failures
- Document solutions
- Track recurring test failures

---

## Quick Reference

### Essential Tests (Every Deployment)

**Functionality**:
- [ ] Homepage loads
- [ ] Main navigation works
- [ ] Contact form submits
- [ ] Search works (if applicable)

**Browser**:
- [ ] Chrome Desktop
- [ ] Chrome Mobile
- [ ] At least one other browser

**Mobile**:
- [ ] Mobile menu works
- [ ] Layout correct
- [ ] No horizontal scrolling

**Performance**:
- [ ] Load time < 3 seconds
- [ ] No console errors
- [ ] No PHP errors

### Test Commands

```bash
# WordPress
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp db check --allow-root
wp core verify-checksums --allow-root
wp plugin list --allow-root

# Bash syntax
bash -n script.sh

# Python syntax
python3 -m py_compile script.py

# HTTP test
curl -I https://rundaverun.org

# Performance test
curl -w "@curl-format.txt" -o /dev/null -s https://rundaverun.org
```

### curl Format File

Create `/home/dave/.curl-format.txt`:
```
time_namelookup:  %{time_namelookup}s\n
time_connect:  %{time_connect}s\n
time_starttransfer:  %{time_starttransfer}s\n
time_total:  %{time_total}s\n
```

---

**This protocol is part of the persistent memory system.**
**Reference before any deployment or code changes.**
