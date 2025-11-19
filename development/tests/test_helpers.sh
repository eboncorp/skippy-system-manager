#!/bin/bash
# Test Helper Functions v1.0.0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test counter
TEST_COUNT=0
PASSED_COUNT=0
FAILED_COUNT=0

# Assert functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"

    if [[ "$expected" == "$actual" ]]; then
        return 0
    else
        echo "❌ $message"
        echo "   Expected: $expected"
        echo "   Actual:   $actual"
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-String not found}"

    if echo "$haystack" | grep -q "$needle"; then
        return 0
    else
        echo "❌ $message"
        echo "   Looking for: $needle"
        echo "   In: $haystack"
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-File does not exist}"

    if [[ -f "$file" ]]; then
        return 0
    else
        echo "❌ $message: $file"
        return 1
    fi
}

assert_command_succeeds() {
    local command="$1"
    local message="${2:-Command failed}"

    if eval "$command" > /dev/null 2>&1; then
        return 0
    else
        echo "❌ $message: $command"
        return 1
    fi
}

# Test runner
run_test() {
    local test_name="$1"
    local test_function="$2"

    TEST_COUNT=$((TEST_COUNT + 1))

    if $test_function; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED_COUNT=$((PASSED_COUNT + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        return 1
    fi
}

# Test summary
test_summary() {
    echo ""
    echo "Tests run: $TEST_COUNT"
    echo "Passed: $PASSED_COUNT"
    echo "Failed: $FAILED_COUNT"

    if [[ $FAILED_COUNT -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}
