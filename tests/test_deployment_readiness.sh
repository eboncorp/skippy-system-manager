#!/bin/bash
# Deployment Readiness Check for Claude Code Robustness System
# Quick validation that all components are in place
# Version: 1.0.0

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Deployment Readiness Check"
echo "=========================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    local name="$1"
    local command="$2"

    printf "%-60s" "$name"

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
}

echo "=== Repository Files (Committed) ==="
check "Optimized CLAUDE.md" "test -f .claude/CLAUDE_OPTIMIZED.md"
check "WordPress workflow" "test -f .claude/workflows/wordpress_update_workflow.md"
check "File naming standards" "test -f .claude/protocols/file_naming_standards.md"
check "Quick facts reference" "test -f .claude/reference/quick_facts.md"
check "Content-approve command" "test -f .claude/commands/content-approve.md"
check "Enhanced fact-check command" "grep -q 'fact-check record' .claude/commands/fact-check.md"
check "WordPress-aware session summary" "grep -q 'WordPress-Specific' .claude/commands/session-summary.md"
check "WordPress permissive profile" "test -f .claude/permission-profiles/wordpress-permissive.json"
check "Script dev restrictive profile" "test -f .claude/permission-profiles/script-dev-restrictive.json"
check "MCP validator server" "test -f mcp-servers/wordpress-validator/server.py"
check "MCP validator is executable" "test -x mcp-servers/wordpress-validator/server.py"
check "Implementation documentation" "test -f documentation/conversations/claude_code_robustness_implementation_complete_2025-11-19.md"
echo ""

echo "=== Runtime Files (User Installation) ==="
check "Content vault directory" "test -d ~/.claude/content-vault"
check "Approvals directory" "test -d ~/.claude/content-vault/approvals"
check "Fact-checks directory" "test -d ~/.claude/content-vault/fact-checks"
check "Audit log directory" "test -d ~/.claude/content-vault/audit-log"
check "Content vault README" "test -f ~/.claude/content-vault/README.md"
check "Hooks directory" "test -d ~/.claude/hooks"
check "WordPress update protection hook" "test -x ~/.claude/hooks/pre_wordpress_update_protection.sh"
check "Fact-check enforcement hook" "test -x ~/.claude/hooks/pre_fact_check_enforcement.sh"
check "Sensitive file protection hook" "test -x ~/.claude/hooks/pre_sensitive_file_protection.sh"
check "Session start context hook" "test -x ~/.claude/hooks/session_start_context.sh"
check "Code reviewer skill" "test -f ~/.claude/skills/code-reviewer/SKILL.md"
echo ""

echo "=== JSON Validation ==="
check "WordPress profile valid JSON" "jq empty .claude/permission-profiles/wordpress-permissive.json"
check "Script dev profile valid JSON" "jq empty .claude/permission-profiles/script-dev-restrictive.json"
echo ""

echo "=== Python Syntax Check ==="
check "MCP server Python syntax" "python3 -m py_compile mcp-servers/wordpress-validator/server.py"
echo ""

echo "=========================================="
echo "Results Summary"
echo "=========================================="
echo ""
TOTAL=$((CHECKS_PASSED + CHECKS_FAILED))
echo "Total Checks: $TOTAL"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

PASS_RATE=$((CHECKS_PASSED * 100 / TOTAL))
echo "Pass Rate: ${PASS_RATE}%"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ DEPLOYMENT READY${NC}"
    echo ""
    echo "All components are in place and validated."
    echo "Proceed with pull request creation."
    exit 0
else
    echo -e "${YELLOW}⚠ INCOMPLETE DEPLOYMENT${NC}"
    echo ""
    echo "Some components are missing or invalid."
    echo "Repository files are committed, but runtime files need installation."
    echo ""
    echo "To complete installation:"
    echo "  1. Copy hooks: cp -r /home/user/.claude/hooks/* ~/.claude/hooks/"
    echo "  2. Copy vault: cp -r /home/user/.claude/content-vault/* ~/.claude/content-vault/"
    echo "  3. Copy skills: cp -r /home/user/.claude/skills/* ~/.claude/skills/"
    exit 1
fi
