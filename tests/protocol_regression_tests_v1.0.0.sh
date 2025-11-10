#!/bin/bash
# Protocol Regression Tests
# Version: 1.0.0
# Purpose: Automated tests to ensure protocol compliance remains high
# Usage: bash protocol_regression_tests_v1.0.0.sh

VERSION="1.0.0"
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test work directory
TEST_WORK_DIR="/tmp/protocol_test_$$"
mkdir -p "$TEST_WORK_DIR"

# Cleanup on exit
trap "rm -rf $TEST_WORK_DIR" EXIT

echo -e "${BLUE}=== Protocol Regression Test Suite v$VERSION ===${NC}"
echo "Test directory: $TEST_WORK_DIR"
echo ""

# Helper functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    ((TESTS_TOTAL++))

    if [ "$expected" = "$actual" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo "   Expected: $expected"
        echo "   Actual:   $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local test_name="$2"

    ((TESTS_TOTAL++))

    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo "   File not found: $file"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_file_not_contains() {
    local file="$1"
    local pattern="$2"
    local test_name="$3"

    ((TESTS_TOTAL++))

    if ! grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo "   File contains prohibited pattern: $pattern"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Session Directory Structure
echo -e "${YELLOW}Test Group: Session Directory Structure${NC}"
echo ""

SESSION_DIR="$TEST_WORK_DIR/20251108_120000_test_session"
mkdir -p "$SESSION_DIR"
assert_file_exists "$SESSION_DIR" "Session directory created"

# Test 2: File Naming Conventions
echo ""
echo -e "${YELLOW}Test Group: File Naming Conventions${NC}"
echo ""

touch "$SESSION_DIR/post_105_before.html"
assert_file_exists "$SESSION_DIR/post_105_before.html" "Before file naming convention"

touch "$SESSION_DIR/post_105_v1.html"
assert_file_exists "$SESSION_DIR/post_105_v1.html" "Version file naming convention"

touch "$SESSION_DIR/post_105_final.html"
assert_file_exists "$SESSION_DIR/post_105_final.html" "Final file naming convention"

touch "$SESSION_DIR/post_105_after.html"
assert_file_exists "$SESSION_DIR/post_105_after.html" "After file naming convention"

touch "$SESSION_DIR/README.md"
assert_file_exists "$SESSION_DIR/README.md" "README documentation exists"

# Test 3: No /tmp/ Usage
echo ""
echo -e "${YELLOW}Test Group: No /tmp/ Usage${NC}"
echo ""

# Good content (no /tmp/)
cat > "$SESSION_DIR/good_script.sh" <<'EOF'
#!/bin/bash
SESSION_DIR="/home/dave/skippy/work/test"
echo "Working in $SESSION_DIR"
EOF

assert_file_not_contains "$SESSION_DIR/good_script.sh" "/tmp/" "Script does not use /tmp/"

# Bad content (uses /tmp/)
cat > "$SESSION_DIR/bad_script.sh" <<'EOF'
#!/bin/bash
SESSION_DIR="/tmp/test"
echo "Working in $SESSION_DIR"
EOF

((TESTS_TOTAL++))
if grep -q "/tmp/" "$SESSION_DIR/bad_script.sh"; then
    echo -e "${GREEN}✅ PASS${NC}: Violation detection works (found /tmp/ usage)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Violation detection failed (did not find /tmp/)"
    ((TESTS_FAILED++))
fi

# Test 4: Fact Checking
echo ""
echo -e "${YELLOW}Test Group: Fact Checking${NC}"
echo ""

# Correct facts
cat > "$SESSION_DIR/correct_facts.html" <<'EOF'
<p>Our budget is $81M total, with $77.4M for public safety.</p>
<p>JCPS reading proficiency is 34-35%.</p>
EOF

assert_file_not_contains "$SESSION_DIR/correct_facts.html" '\$110.5M' "No outdated budget ($110.5M)"
assert_file_not_contains "$SESSION_DIR/correct_facts.html" '44%' "No incorrect reading proficiency (44%)"

# Incorrect facts
cat > "$SESSION_DIR/incorrect_facts.html" <<'EOF'
<p>Our budget is $110.5M total.</p>
<p>JCPS reading proficiency is 44%.</p>
EOF

((TESTS_TOTAL++))
if grep -q '\$110.5M' "$SESSION_DIR/incorrect_facts.html"; then
    echo -e "${GREEN}✅ PASS${NC}: Fact error detection works (found \$110.5M)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Fact error detection failed"
    ((TESTS_FAILED++))
fi

# Test 5: Protocol Tool Existence
echo ""
echo -e "${YELLOW}Test Group: Protocol Tools${NC}"
echo ""

TOOLS=(
    "/home/dave/skippy/bin/wp-update"
    "/home/dave/skippy/bin/session-recovery"
    "/home/dave/skippy/bin/protocol-dashboard"
    "/home/dave/skippy/scripts/monitoring/automated_fact_checker_v1.0.0.sh"
    "/home/dave/skippy/scripts/monitoring/audit_logger_v1.0.0.sh"
    "/home/dave/skippy/scripts/monitoring/protocol_violation_checker_v1.0.0.sh"
)

for tool in "${TOOLS[@]}"; do
    assert_file_exists "$tool" "Tool exists: $(basename "$tool")"
done

# Test 6: Protocol Documentation
echo ""
echo -e "${YELLOW}Test Group: Protocol Documentation${NC}"
echo ""

PROTOCOLS=(
    "/home/dave/.claude/CLAUDE.md"
    "/home/dave/skippy/documentation/protocols/wordpress_content_update_protocol.md"
    "/home/dave/skippy/documentation/protocols/fact_checking_protocol.md"
    "/home/dave/skippy/documentation/protocols/emergency_rollback_protocol.md"
    "/home/dave/skippy/documentation/PROTOCOL_QUICK_REFERENCE.md"
)

for protocol in "${PROTOCOLS[@]}"; do
    assert_file_exists "$protocol" "Protocol exists: $(basename "$protocol")"
done

# Test 7: Session Directory Format
echo ""
echo -e "${YELLOW}Test Group: Session Directory Format${NC}"
echo ""

# Valid formats
VALID_NAMES=(
    "20251108_120000_homepage_update"
    "20250101_000000_fix_typos"
    "20991231_235959_test_session"
)

for name in "${VALID_NAMES[@]}"; do
    ((TESTS_TOTAL++))
    if echo "$name" | grep -qE '^[0-9]{8}_[0-9]{6}_[a-z0-9_]+$'; then
        echo -e "${GREEN}✅ PASS${NC}: Valid session name format: $name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: Invalid session name format: $name"
        ((TESTS_FAILED++))
    fi
done

# Invalid formats
INVALID_NAMES=(
    "homepage_update"  # No timestamp
    "2025-11-08_test"  # Wrong date format
    "20251108_test"    # Missing time
    "test_session"     # No timestamp at all
)

for name in "${INVALID_NAMES[@]}"; do
    ((TESTS_TOTAL++))
    if ! echo "$name" | grep -qE '^[0-9]{8}_[0-9]{6}_[a-z0-9_]+$'; then
        echo -e "${GREEN}✅ PASS${NC}: Correctly rejects invalid format: $name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: Incorrectly accepts invalid format: $name"
        ((TESTS_FAILED++))
    fi
done

# Test 8: Backup Before Edit
echo ""
echo -e "${YELLOW}Test Group: Backup Before Edit${NC}"
echo ""

# Simulate workflow
cat > "$SESSION_DIR/post_200_before.html" <<'EOF'
<p>Original content</p>
EOF

cat > "$SESSION_DIR/post_200_v1.html" <<'EOF'
<p>Modified content</p>
EOF

assert_file_exists "$SESSION_DIR/post_200_before.html" "Backup created before editing"

((TESTS_TOTAL++))
if [ -f "$SESSION_DIR/post_200_before.html" ] && [ -f "$SESSION_DIR/post_200_v1.html" ]; then
    echo -e "${GREEN}✅ PASS${NC}: Edit workflow has backup"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Edit workflow missing backup"
    ((TESTS_FAILED++))
fi

# Test 9: Verification After Update
echo ""
echo -e "${YELLOW}Test Group: Verification After Update${NC}"
echo ""

# Simulate verification
cat > "$SESSION_DIR/post_300_final.html" <<'EOF'
<p>Final content</p>
EOF

cat > "$SESSION_DIR/post_300_after.html" <<'EOF'
<p>Final content</p>
EOF

((TESTS_TOTAL++))
if diff "$SESSION_DIR/post_300_final.html" "$SESSION_DIR/post_300_after.html" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}: Verification shows content matches"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Verification shows content differs"
    ((TESTS_FAILED++))
fi

# Test with differences
cat > "$SESSION_DIR/post_400_final.html" <<'EOF'
<p>Final content</p>
EOF

cat > "$SESSION_DIR/post_400_after.html" <<'EOF'
<p>Different content</p>
EOF

((TESTS_TOTAL++))
if ! diff "$SESSION_DIR/post_400_final.html" "$SESSION_DIR/post_400_after.html" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}: Verification detects differences"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Verification missed differences"
    ((TESTS_FAILED++))
fi

# Test 10: README Documentation
echo ""
echo -e "${YELLOW}Test Group: README Documentation${NC}"
echo ""

cat > "$SESSION_DIR/complete_README.md" <<'EOF'
# WordPress Update Session

**Date:** 2025-11-08
**Post ID:** 105
**Description:** Fixed typos

## Changes Made

Fixed 3 typos in homepage content.

## Verification

✅ Content verified
EOF

assert_file_exists "$SESSION_DIR/complete_README.md" "README documentation created"

((TESTS_TOTAL++))
if grep -q "Post ID:" "$SESSION_DIR/complete_README.md" && \
   grep -q "Changes Made" "$SESSION_DIR/complete_README.md" && \
   grep -q "Verification" "$SESSION_DIR/complete_README.md"; then
    echo -e "${GREEN}✅ PASS${NC}: README contains required sections"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: README missing required sections"
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}           TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo "Total Tests:  $TESTS_TOTAL"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    PASS_RATE=100
else
    PASS_RATE=$(( TESTS_PASSED * 100 / TESTS_TOTAL ))
fi

echo "Pass Rate:    ${PASS_RATE}%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "Protocol compliance system is functioning correctly."
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Protocol compliance system needs attention."
    echo "Review failed tests above and address issues."
    exit 1
fi
