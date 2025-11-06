#!/bin/bash
# Comprehensive Debug and Validation Script
# Version: 1.0.0
# Purpose: Run all validation checks and generate debug report

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  Skippy Debug & Validation${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Function to run a check
run_check() {
    local name="$1"
    local command="$2"

    echo -n "Checking $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to run a check with warning
run_check_warn() {
    local name="$1"
    local command="$2"

    echo -n "Checking $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠ WARNING${NC}"
        ((WARNINGS++))
        return 1
    fi
}

echo -e "${BLUE}=== Python Checks ===${NC}"
run_check "Python availability" "which python3"
run_check "Python version >= 3.8" "python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'"
run_check "skippy_logger syntax" "python3 -m py_compile lib/python/skippy_logger.py"
run_check "skippy_validator syntax" "python3 -m py_compile lib/python/skippy_validator.py"
run_check "skippy_logger imports" "python3 -c 'import sys; sys.path.insert(0, \"lib/python\"); from skippy_logger import get_logger'"
run_check "skippy_validator imports" "python3 -c 'import sys; sys.path.insert(0, \"lib/python\"); from skippy_validator import validate_path'"

echo ""
echo -e "${BLUE}=== Shell Script Checks ===${NC}"
run_check "Bash availability" "which bash"
run_check "validate_config.sh syntax" "bash -n scripts/utility/validate_config.sh"
run_check "consolidate_legacy.sh syntax" "bash -n scripts/maintenance/consolidate_legacy_v1.0.0.sh"

echo ""
echo -e "${BLUE}=== Configuration File Checks ===${NC}"
run_check "config.env.example exists" "test -f config.env.example"
run_check "pytest.ini exists" "test -f pytest.ini"
run_check "pyproject.toml exists" "test -f pyproject.toml"
run_check "pyproject.toml TOML syntax" "python3 -c 'import tomllib; tomllib.load(open(\"pyproject.toml\", \"rb\"))'"
run_check ".pre-commit-config.yaml YAML syntax" "python3 -c 'import yaml; yaml.safe_load(open(\".pre-commit-config.yaml\"))'"
run_check "docker-compose.yml YAML syntax" "python3 -c 'import yaml; yaml.safe_load(open(\"docker-compose.yml\"))'"
run_check ".github/workflows/ci.yml YAML syntax" "python3 -c 'import yaml; yaml.safe_load(open(\".github/workflows/ci.yml\"))'"
run_check ".markdownlint.json JSON syntax" "python3 -c 'import json; json.load(open(\".markdownlint.json\"))'"

echo ""
echo -e "${BLUE}=== Documentation Checks ===${NC}"
run_check "README.md exists" "test -f README.md"
run_check "PROJECT_ARCHITECTURE.md exists" "test -f PROJECT_ARCHITECTURE.md"
run_check "SCRIPT_STATUS.md exists" "test -f SCRIPT_STATUS.md"
run_check "CONTRIBUTING.md exists" "test -f CONTRIBUTING.md"
run_check "SECURITY.md exists" "test -f SECURITY.md"

echo ""
echo -e "${BLUE}=== Docker Checks ===${NC}"
run_check "Dockerfile exists" "test -f Dockerfile"
run_check "docker-compose.yml exists" "test -f docker-compose.yml"
run_check ".dockerignore exists" "test -f .dockerignore"
run_check_warn "Docker available" "which docker"

echo ""
echo -e "${BLUE}=== Build Tool Checks ===${NC}"
run_check "Makefile exists" "test -f Makefile"
run_check "Makefile syntax" "make -n help"
run_check "make info works" "make info"

echo ""
echo -e "${BLUE}=== Test File Checks ===${NC}"
run_check "tests/ directory exists" "test -d tests"
run_check "tests/conftest.py exists" "test -f tests/conftest.py"
run_check "Unit tests exist" "test -d tests/unit && ls tests/unit/test_*.py > /dev/null 2>&1"
run_check "Integration tests exist" "test -d tests/integration && ls tests/integration/test_*.py > /dev/null 2>&1"

echo ""
echo -e "${BLUE}=== GitHub Checks ===${NC}"
run_check ".github/workflows exists" "test -d .github/workflows"
run_check "CI workflow exists" "test -f .github/workflows/ci.yml"
run_check "Issue templates exist" "test -d .github/ISSUE_TEMPLATE"
run_check "PR template exists" "test -f .github/PULL_REQUEST_TEMPLATE.md"

echo ""
echo -e "${BLUE}=== Optional Tool Checks ===${NC}"
run_check_warn "ShellCheck available" "which shellcheck"
run_check_warn "pytest available" "which pytest"
run_check_warn "pylint available" "which pylint"
run_check_warn "flake8 available" "which flake8"
run_check_warn "black available" "which black"
run_check_warn "pre-commit available" "which pre-commit"

echo ""
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  Results${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Passed:   ${PASSED}${NC}"
echo -e "${RED}Failed:   ${FAILED}${NC}"
echo -e "${YELLOW}Warnings: ${WARNINGS}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review above.${NC}"
    exit 1
fi
