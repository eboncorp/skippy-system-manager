#!/bin/bash
# Test Suite for Claude Code Robustness System
# Tests all enforcement hooks and workflows
# Version: 1.0.0
# Created: 2025-11-19

set -euo pipefail

echo "=================================="
echo "Claude Code Robustness Test Suite"
echo "=================================="
echo ""

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"  # "pass" or "fail"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo "Test $TESTS_RUN: $test_name"

    if eval "$test_command" 2>&1 | grep -q "$expected_result"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Create test session directory
TEST_SESSION="/tmp/robustness_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_SESSION"
echo "Test session: $TEST_SESSION"
echo ""

# ==========================================
# TEST CATEGORY 1: Content Vault Infrastructure
# ==========================================
echo "=== Testing Content Vault Infrastructure ==="
echo ""

# Test 1: Verify content vault directories exist
run_test "Content vault directories exist" \
    "test -d ~/.claude/content-vault/approvals && test -d ~/.claude/content-vault/fact-checks && test -d ~/.claude/content-vault/audit-log" \
    ""

# Test 2: Create test fact-check record
echo "Creating test fact-check record..."
cat > ~/.claude/content-vault/fact-checks/999_test_$(date +%Y%m%d_%H%M%S).fact-checked <<EOF
{
  "page_id": 999,
  "timestamp": "$(date -Iseconds)",
  "expires": "$(date -Iseconds -d '+1 hour')",
  "facts_verified": [
    {"claim": "Test fact", "verified": true}
  ],
  "checker": "test-suite",
  "status": "verified"
}
EOF

run_test "Fact-check record created" \
    "test -f ~/.claude/content-vault/fact-checks/999_test_*.fact-checked" \
    ""

# Test 3: Create test approval record
echo "Creating test approval record..."
cat > ~/.claude/content-vault/approvals/999_test_$(date +%Y%m%d_%H%M%S).approved <<EOF
{
  "page_id": 999,
  "approver": "test-suite",
  "timestamp": "$(date -Iseconds)",
  "expires": "$(date -Iseconds -d '+24 hours')",
  "notes": "Test approval"
}
EOF

run_test "Approval record created" \
    "test -f ~/.claude/content-vault/approvals/999_test_*.approved" \
    ""

# ==========================================
# TEST CATEGORY 2: Hook Validation
# ==========================================
echo "=== Testing Hook Files ==="
echo ""

# Test 4: WordPress update protection hook exists and executable
run_test "WordPress update hook exists and executable" \
    "test -x ~/.claude/hooks/pre_wordpress_update_protection.sh" \
    ""

# Test 5: Fact-check enforcement hook exists and executable
run_test "Fact-check enforcement hook exists and executable" \
    "test -x ~/.claude/hooks/pre_fact_check_enforcement.sh" \
    ""

# Test 6: Sensitive file protection hook exists and executable
run_test "Sensitive file protection hook exists and executable" \
    "test -x ~/.claude/hooks/pre_sensitive_file_protection.sh" \
    ""

# Test 7: Session start context hook exists and executable
run_test "Session start context hook exists and executable" \
    "test -x ~/.claude/hooks/session_start_context.sh" \
    ""

# Test 8: All hooks have proper shebang
run_test "All hooks have proper shebang" \
    "grep -l '^#!/bin/bash' ~/.claude/hooks/*.sh | wc -l" \
    "4"

# ==========================================
# TEST CATEGORY 3: Progressive Disclosure
# ==========================================
echo "=== Testing Progressive Disclosure Structure ==="
echo ""

# Test 9: Optimized CLAUDE.md exists
run_test "Optimized CLAUDE.md exists" \
    "test -f .claude/CLAUDE_OPTIMIZED.md" \
    ""

# Test 10: Workflows directory exists with files
run_test "Workflows directory has files" \
    "test -d .claude/workflows && ls .claude/workflows/*.md" \
    "wordpress_update_workflow"

# Test 11: Protocols directory exists with files
run_test "Protocols directory has files" \
    "test -d .claude/protocols && ls .claude/protocols/*.md" \
    "file_naming_standards"

# Test 12: Reference directory exists with files
run_test "Reference directory has files" \
    "test -d .claude/reference && ls .claude/reference/*.md" \
    "quick_facts"

# ==========================================
# TEST CATEGORY 4: Commands
# ==========================================
echo "=== Testing Command Files ==="
echo ""

# Test 13: content-approve command exists
run_test "content-approve command exists" \
    "test -f .claude/commands/content-approve.md" \
    ""

# Test 14: fact-check command enhanced
run_test "fact-check command has vault integration" \
    "grep -q 'fact-check record' .claude/commands/fact-check.md" \
    ""

# Test 15: session-summary enhanced for WordPress
run_test "session-summary has WordPress context" \
    "grep -q 'WordPress-Specific Context' .claude/commands/session-summary.md" \
    ""

# ==========================================
# TEST CATEGORY 5: Skills
# ==========================================
echo "=== Testing Skills ==="
echo ""

# Test 16: Code reviewer skill exists
run_test "Code reviewer skill exists" \
    "test -f ~/.claude/skills/code-reviewer/SKILL.md" \
    ""

# Test 17: Code reviewer has YAML frontmatter
run_test "Code reviewer skill has proper frontmatter" \
    "head -5 ~/.claude/skills/code-reviewer/SKILL.md | grep -q 'name: code-reviewer'" \
    ""

# Test 18: Code reviewer specifies allowed tools
run_test "Code reviewer has tool restrictions" \
    "grep -q 'allowed-tools' ~/.claude/skills/code-reviewer/SKILL.md" \
    ""

# ==========================================
# TEST CATEGORY 6: MCP Server
# ==========================================
echo "=== Testing MCP Server ==="
echo ""

# Test 19: WordPress validator server exists
run_test "WordPress validator MCP server exists" \
    "test -f mcp-servers/wordpress-validator/server.py" \
    ""

# Test 20: MCP server is executable
run_test "MCP server is executable" \
    "test -x mcp-servers/wordpress-validator/server.py" \
    ""

# Test 21: MCP server has proper shebang
run_test "MCP server has Python shebang" \
    "head -1 mcp-servers/wordpress-validator/server.py | grep -q '#!/usr/bin/env python3'" \
    ""

# Test 22: MCP server has validation classes
run_test "MCP server has validator class" \
    "grep -q 'class WordPressContentValidator' mcp-servers/wordpress-validator/server.py" \
    ""

# ==========================================
# TEST CATEGORY 7: Permission Profiles
# ==========================================
echo "=== Testing Permission Profiles ==="
echo ""

# Test 23: WordPress permissive profile exists
run_test "WordPress permissive profile exists" \
    "test -f .claude/permission-profiles/wordpress-permissive.json" \
    ""

# Test 24: Script dev restrictive profile exists
run_test "Script dev restrictive profile exists" \
    "test -f .claude/permission-profiles/script-dev-restrictive.json" \
    ""

# Test 25: WordPress profile has valid JSON
run_test "WordPress profile is valid JSON" \
    "jq . .claude/permission-profiles/wordpress-permissive.json" \
    "wordpress-permissive"

# Test 26: Script dev profile has valid JSON
run_test "Script dev profile is valid JSON" \
    "jq . .claude/permission-profiles/script-dev-restrictive.json" \
    "script-dev-restrictive"

# ==========================================
# TEST CATEGORY 8: Documentation
# ==========================================
echo "=== Testing Documentation ==="
echo ""

# Test 27: Implementation summary exists
run_test "Implementation summary exists" \
    "test -f documentation/conversations/claude_code_robustness_implementation_complete_2025-11-19.md" \
    ""

# Test 28: Content vault README exists
run_test "Content vault README exists" \
    "test -f ~/.claude/content-vault/README.md" \
    ""

# Test 29: WordPress workflow documentation exists
run_test "WordPress workflow documentation exists" \
    "test -f .claude/workflows/wordpress_update_workflow.md" \
    ""

# Test 30: Permission profiles README exists
run_test "Permission profiles README exists" \
    "test -f .claude/permission-profiles/README.md" \
    ""

# ==========================================
# CLEANUP
# ==========================================
echo "=== Cleanup ==="
echo ""

# Remove test records
rm -f ~/.claude/content-vault/fact-checks/999_test_*.fact-checked
rm -f ~/.claude/content-vault/approvals/999_test_*.approved
rm -rf "$TEST_SESSION"

echo "Test records cleaned up"
echo ""

# ==========================================
# SUMMARY
# ==========================================
echo "=========================================="
echo "Test Suite Summary"
echo "=========================================="
echo "Total Tests:  $TESTS_RUN"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed:       $TESTS_FAILED${NC}"
fi
echo ""

# Calculate percentage
PASS_RATE=$((TESTS_PASSED * 100 / TESTS_RUN))
echo "Pass Rate: ${PASS_RATE}%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo ""
    echo "The Claude Code Robustness System is ready for deployment."
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review failed tests before deployment."
    exit 1
fi
