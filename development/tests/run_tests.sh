#!/bin/bash
# Skippy Test Suite Runner v1.0.0
# Unified testing framework for all scripts

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$TEST_DIR/results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "═══════════════════════════════════════════════════"
echo "  Skippy Test Suite"
echo "═══════════════════════════════════════════════════"
echo "Started: $(date)"
echo "Results: $RESULTS_DIR"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test categories
CATEGORIES=(
    "automation"
    "wordpress"
    "security"
    "monitoring"
    "integration"
)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

run_test_file() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .sh)

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # Run test and capture output
    if bash "$test_file" > "$RESULTS_DIR/${test_name}.log" 2>&1; then
        echo -e "  ${GREEN}✓${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "  ${RED}✗${NC} $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "    Error log: $RESULTS_DIR/${test_name}.log"
        tail -3 "$RESULTS_DIR/${test_name}.log" | sed 's/^/    /'
        return 1
    fi
}

# Run tests by category
for category in "${CATEGORIES[@]}"; do
    CAT_DIR="$TEST_DIR/$category"

    if [[ ! -d "$CAT_DIR" ]]; then
        continue
    fi

    TEST_FILES=$(find "$CAT_DIR" -name "test_*.sh" -type f 2>/dev/null)

    if [[ -z "$TEST_FILES" ]]; then
        continue
    fi

    echo "Testing: $category"

    while IFS= read -r test_file; do
        run_test_file "$test_file"
    done <<< "$TEST_FILES"

    echo ""
done

# Summary
echo "═══════════════════════════════════════════════════"
echo "  Test Results"
echo "═══════════════════════════════════════════════════"
echo "Total:   $TOTAL_TESTS"
echo -e "${GREEN}Passed:  $PASSED_TESTS${NC}"
echo -e "${RED}Failed:  $FAILED_TESTS${NC}"

if [[ $SKIPPED_TESTS -gt 0 ]]; then
    echo -e "${YELLOW}Skipped: $SKIPPED_TESTS${NC}"
fi

if [[ $TOTAL_TESTS -gt 0 ]]; then
    SUCCESS_RATE=$(echo "scale=2; $PASSED_TESTS*100/$TOTAL_TESTS" | bc)
    echo "Success Rate: ${SUCCESS_RATE}%"
fi

echo ""
echo "Results saved to: $RESULTS_DIR"
echo ""

# Exit code
if [[ $FAILED_TESTS -gt 0 ]]; then
    exit 1
else
    exit 0
fi
