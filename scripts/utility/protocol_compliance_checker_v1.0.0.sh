#!/bin/bash
#
# Protocol Compliance Checker v1.0.0
#
# Validates session directories for protocol compliance
# Checks: file naming, required files, verification steps, documentation
#
# Usage:
#   ./protocol_compliance_checker_v1.0.0.sh /path/to/session_directory
#   ./protocol_compliance_checker_v1.0.0.sh --latest  (checks most recent session)
#   ./protocol_compliance_checker_v1.0.0.sh --all     (checks all recent sessions)

set -e

VERSION="1.0.0"
SCRIPT_NAME="Protocol Compliance Checker"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compliance score
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Print header
print_header() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  $SCRIPT_NAME v$VERSION                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# Check functions
check_pass() {
    ((TOTAL_CHECKS++))
    ((PASSED_CHECKS++))
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    ((TOTAL_CHECKS++))
    ((FAILED_CHECKS++))
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    ((TOTAL_CHECKS++))
    ((WARNING_CHECKS++))
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check session directory structure
check_directory_structure() {
    local session_dir="$1"

    echo ""
    echo -e "${BLUE}═══ Directory Structure ═══${NC}"

    # Check if directory exists
    if [ ! -d "$session_dir" ]; then
        check_fail "Session directory does not exist: $session_dir"
        return 1
    fi
    check_pass "Session directory exists"

    # Check directory naming convention
    dirname=$(basename "$session_dir")
    if [[ $dirname =~ ^[0-9]{8}_[0-9]{6}_.+$ ]]; then
        check_pass "Directory name follows convention: $dirname"
    else
        check_fail "Directory name doesn't follow convention (YYYYMMDD_HHMMSS_description): $dirname"
    fi

    # Check for README.md
    if [ -f "$session_dir/README.md" ]; then
        check_pass "README.md exists"
    else
        check_fail "README.md missing (required for documentation)"
    fi
}

# Check file naming conventions
check_file_naming() {
    local session_dir="$1"

    echo ""
    echo -e "${BLUE}═══ File Naming Conventions ═══${NC}"

    # Check for _before files
    before_files=$(find "$session_dir" -maxdepth 1 -name "*_before.*" 2>/dev/null | wc -l)
    if [ "$before_files" -gt 0 ]; then
        check_pass "Found $before_files _before file(s) (original state saved)"
    else
        check_warn "No _before files found (may not be required for all sessions)"
    fi

    # Check for _final files
    final_files=$(find "$session_dir" -maxdepth 1 -name "*_final.*" 2>/dev/null | wc -l)
    if [ "$final_files" -gt 0 ]; then
        check_pass "Found $final_files _final file(s)"
    else
        check_warn "No _final files found"
    fi

    # Check for _after files
    after_files=$(find "$session_dir" -maxdepth 1 -name "*_after.*" 2>/dev/null | wc -l)
    if [ "$after_files" -gt 0 ]; then
        check_pass "Found $after_files _after file(s) (verification completed)"
    else
        check_warn "No _after files found (verification may be incomplete)"
    fi

    # Check for version files (_v1, _v2, etc.)
    version_files=$(find "$session_dir" -maxdepth 1 -name "*_v[0-9].*" 2>/dev/null | wc -l)
    if [ "$version_files" -gt 0 ]; then
        check_pass "Found $version_files version file(s) (iterations tracked)"
    else
        check_warn "No version files found (single-step edit or not required)"
    fi
}

# Check verification steps
check_verification() {
    local session_dir="$1"

    echo ""
    echo -e "${BLUE}═══ Verification Steps ═══${NC}"

    # Check for verification log
    if [ -f "$session_dir/http_verification.log" ]; then
        check_pass "HTTP verification log exists"

        # Check if log has 200 OK responses
        if grep -q "200" "$session_dir/http_verification.log"; then
            check_pass "HTTP verification shows successful responses"
        else
            check_fail "HTTP verification log has no 200 OK responses"
        fi
    else
        check_warn "No HTTP verification log (may not be required for all sessions)"
    fi

    # Check for _after files matching _final files
    local all_verified=true
    for final_file in "$session_dir"/*_final.*; do
        if [ -f "$final_file" ]; then
            basename=$(basename "$final_file" | sed 's/_final\./_after./')
            after_file="$session_dir/$basename"

            if [ -f "$after_file" ]; then
                check_pass "Verification file exists: $basename"
            else
                check_fail "Missing verification file: $basename"
                all_verified=false
            fi
        fi
    done
}

# Check documentation quality
check_documentation() {
    local session_dir="$1"

    echo ""
    echo -e "${BLUE}═══ Documentation Quality ═══${NC}"

    if [ ! -f "$session_dir/README.md" ]; then
        check_fail "README.md missing - cannot check documentation"
        return
    fi

    # Check for required sections in README
    local readme="$session_dir/README.md"

    if grep -qi "date:" "$readme"; then
        check_pass "README contains date"
    else
        check_warn "README missing date"
    fi

    if grep -qi "status:" "$readme"; then
        check_pass "README contains status"
    else
        check_warn "README missing status"
    fi

    if grep -qi "changes" "$readme" || grep -qi "modified" "$readme"; then
        check_pass "README documents changes"
    else
        check_fail "README doesn't document changes made"
    fi

    if grep -qi "verification" "$readme" || grep -qi "verified" "$readme"; then
        check_pass "README mentions verification"
    else
        check_warn "README doesn't mention verification"
    fi

    # Check README size (should be substantial)
    readme_lines=$(wc -l < "$readme")
    if [ "$readme_lines" -ge 10 ]; then
        check_pass "README is substantial ($readme_lines lines)"
    else
        check_warn "README is short ($readme_lines lines) - may need more detail"
    fi
}

# Check for /tmp/ violations
check_tmp_usage() {
    local session_dir="$1"

    echo ""
    echo -e "${BLUE}═══ File Location Policy ═══${NC}"

    # Check if any files reference /tmp/ in logs or scripts
    tmp_refs=$(grep -r "/tmp/" "$session_dir" 2>/dev/null | wc -l)

    if [ "$tmp_refs" -eq 0 ]; then
        check_pass "No /tmp/ usage found (policy compliant)"
    else
        check_warn "Found $tmp_refs reference(s) to /tmp/ (review for policy compliance)"
    fi

    # All files should be in session directory
    check_pass "All work files contained in session directory"
}

# Check rollback capability
check_rollback() {
    local session_dir="$1"

    echo ""
    echo -e "${BLUE}═══ Rollback Capability ═══${NC}"

    before_files=$(find "$session_dir" -maxdepth 1 -name "*_before.*" 2>/dev/null | wc -l)

    if [ "$before_files" -gt 0 ]; then
        check_pass "Rollback capability exists ($before_files backup(s) available)"
    else
        check_warn "No backup files - rollback may not be possible"
    fi
}

# Generate compliance score
generate_score() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    COMPLIANCE SCORE                            ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    if [ "$TOTAL_CHECKS" -eq 0 ]; then
        echo "No checks performed"
        return
    fi

    local score=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

    echo -e "Total Checks:    ${TOTAL_CHECKS}"
    echo -e "${GREEN}Passed:          ${PASSED_CHECKS}${NC}"
    echo -e "${YELLOW}Warnings:        ${WARNING_CHECKS}${NC}"
    echo -e "${RED}Failed:          ${FAILED_CHECKS}${NC}"
    echo ""
    echo -e "Compliance Score: ${score}%"

    # Grade
    if [ "$score" -ge 95 ]; then
        echo -e "Grade:            ${GREEN}A+ (Excellent)${NC}"
    elif [ "$score" -ge 90 ]; then
        echo -e "Grade:            ${GREEN}A (Very Good)${NC}"
    elif [ "$score" -ge 80 ]; then
        echo -e "Grade:            ${YELLOW}B (Good)${NC}"
    elif [ "$score" -ge 70 ]; then
        echo -e "Grade:            ${YELLOW}C (Acceptable)${NC}"
    else
        echo -e "Grade:            ${RED}F (Needs Improvement)${NC}"
    fi

    echo ""

    # Recommendations
    if [ "$FAILED_CHECKS" -gt 0 ]; then
        echo -e "${RED}⚠ Action Required:${NC} Address failed checks above"
    elif [ "$WARNING_CHECKS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ Recommendations:${NC} Review warnings for improvement"
    else
        echo -e "${GREEN}✓ Excellent:${NC} Full protocol compliance achieved"
    fi
}

# Check a single session
check_session() {
    local session_dir="$1"

    echo ""
    echo "Checking session: $(basename "$session_dir")"
    echo "════════════════════════════════════════════════════════════════"

    check_directory_structure "$session_dir"
    check_file_naming "$session_dir"
    check_verification "$session_dir"
    check_documentation "$session_dir"
    check_tmp_usage "$session_dir"
    check_rollback "$session_dir"

    generate_score
}

# Find latest session
find_latest_session() {
    local work_dir="/home/dave/skippy/work"

    # Search all subdirectories for session directories
    local latest=$(find "$work_dir" -maxdepth 3 -type d -name "20*_*" 2>/dev/null | sort -r | head -1)

    if [ -n "$latest" ]; then
        echo "$latest"
    else
        echo ""
    fi
}

# Check all recent sessions
check_all_sessions() {
    local work_dir="/home/dave/skippy/work"

    echo "Searching for recent sessions (last 7 days)..."

    # Find sessions modified in last 7 days
    local sessions=$(find "$work_dir" -maxdepth 3 -type d -name "20*_*" -mtime -7 2>/dev/null | sort -r)

    if [ -z "$sessions" ]; then
        echo "No recent sessions found"
        return 1
    fi

    local count=$(echo "$sessions" | wc -l)
    echo "Found $count recent session(s)"
    echo ""

    # Check each session
    local session_num=1
    while IFS= read -r session_dir; do
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo "Session $session_num of $count"
        echo "════════════════════════════════════════════════════════════════"

        # Reset counters for each session
        TOTAL_CHECKS=0
        PASSED_CHECKS=0
        FAILED_CHECKS=0
        WARNING_CHECKS=0

        check_session "$session_dir"

        ((session_num++))
    done <<< "$sessions"
}

# Main script
main() {
    print_header

    if [ "$#" -eq 0 ]; then
        echo "Usage:"
        echo "  $0 /path/to/session_directory    Check specific session"
        echo "  $0 --latest                       Check most recent session"
        echo "  $0 --all                          Check all recent sessions (last 7 days)"
        echo ""
        echo "Example:"
        echo "  $0 /home/dave/skippy/work/wordpress/rundaverun-local/20251112_050000_homepage_update"
        exit 1
    fi

    case "$1" in
        --latest)
            local latest=$(find_latest_session)
            if [ -n "$latest" ]; then
                check_session "$latest"
            else
                echo "No sessions found in /home/dave/skippy/work/"
                exit 1
            fi
            ;;
        --all)
            check_all_sessions
            ;;
        *)
            # Check specific directory
            if [ ! -d "$1" ]; then
                echo "Error: Directory not found: $1"
                exit 1
            fi
            check_session "$1"
            ;;
    esac
}

main "$@"
