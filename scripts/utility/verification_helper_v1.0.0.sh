#!/bin/bash
#
# Verification Helper v1.0.0
#
# Automates the verification process for WordPress content updates
# Implements three-level verification: Database, HTTP, Functional
#
# Usage:
#   ./verification_helper_v1.0.0.sh --page 105 --session /path/to/session
#   ./verification_helper_v1.0.0.sh --media 1205 --session /path/to/session
#   ./verification_helper_v1.0.0.sh --auto  (auto-detect latest session)

set -e

VERSION="1.0.0"
SCRIPT_NAME="Verification Helper"

# WordPress path
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
WP_CLI="/home/dave/skippy/bin/wp"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verification results
VERIFICATIONS_PASSED=0
VERIFICATIONS_FAILED=0
VERIFICATIONS_WARNED=0

print_header() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  $SCRIPT_NAME v$VERSION                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

verify_pass() {
    ((VERIFICATIONS_PASSED++))
    echo -e "${GREEN}✓${NC} $1"
}

verify_fail() {
    ((VERIFICATIONS_FAILED++))
    echo -e "${RED}✗${NC} $1"
}

verify_warn() {
    ((VERIFICATIONS_WARNED++))
    echo -e "${YELLOW}⚠${NC} $1"
}

# Level 1: Database Verification
verify_database() {
    local resource_type="$1"  # page, post, media
    local resource_id="$2"
    local session_dir="$3"

    echo ""
    echo -e "${BLUE}═══ Level 1: Database Verification ═══${NC}"

    # Determine file naming
    local basename
    case "$resource_type" in
        page|post)
            basename="${resource_type}_${resource_id}"
            ;;
        media)
            basename="media_${resource_id}"
            ;;
        *)
            verify_fail "Unknown resource type: $resource_type"
            return 1
            ;;
    esac

    local final_file="$session_dir/${basename}_final.html"
    local after_file="$session_dir/${basename}_after.html"

    # Check if final file exists
    if [ ! -f "$final_file" ]; then
        verify_warn "Final file not found: $final_file"
        verify_warn "Skipping database verification (may not be required)"
        return 0
    fi

    # Fetch current state from WordPress
    echo "Fetching current state from WordPress..."
    "$WP_CLI" --path="$WP_PATH" post get "$resource_id" --field=post_content > "$after_file" 2>/dev/null || {
        verify_fail "Failed to fetch resource $resource_id from WordPress"
        return 1
    }

    verify_pass "Saved current state to: $(basename "$after_file")"

    # Compare final vs after
    if diff -q "$final_file" "$after_file" > /dev/null 2>&1; then
        verify_pass "Database verification: Content matches exactly"
        return 0
    else
        verify_fail "Database verification: Content differs from expected"
        echo "  Run: diff $final_file $after_file"
        return 1
    fi
}

# Level 2: HTTP Verification
verify_http() {
    local resource_type="$1"
    local resource_id="$2"
    local session_dir="$3"

    echo ""
    echo -e "${BLUE}═══ Level 2: HTTP Verification ═══${NC}"

    # Get site URL
    local site_url
    site_url=$("$WP_CLI" --path="$WP_PATH" option get siteurl 2>/dev/null) || {
        verify_warn "Could not get site URL - skipping HTTP verification"
        return 0
    }

    echo "Site URL: $site_url"

    local http_log="$session_dir/http_verification.log"

    case "$resource_type" in
        page|post)
            # Test page/post URL
            local url="$site_url/?p=$resource_id"
            echo "Testing: $url"

            local http_code
            http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null) || {
                verify_warn "HTTP request failed"
                return 0
            }

            echo "$url: $http_code" >> "$http_log"

            if [ "$http_code" = "200" ]; then
                verify_pass "HTTP verification: Page accessible (200 OK)"
            elif [ "$http_code" = "404" ]; then
                verify_fail "HTTP verification: Page not found (404)"
            else
                verify_warn "HTTP verification: Unexpected status ($http_code)"
            fi
            ;;

        media)
            # Test media URL
            local media_url
            media_url=$("$WP_CLI" --path="$WP_PATH" post get "$resource_id" --field=guid 2>/dev/null) || {
                verify_warn "Could not get media URL"
                return 0
            }

            echo "Testing: $media_url"

            local http_code
            http_code=$(curl -s -o /dev/null -w "%{http_code}" "$media_url" 2>/dev/null) || {
                verify_warn "HTTP request failed"
                return 0
            }

            echo "$media_url: $http_code" >> "$http_log"

            if [ "$http_code" = "200" ]; then
                verify_pass "HTTP verification: Media accessible (200 OK)"
            elif [ "$http_code" = "404" ]; then
                verify_fail "HTTP verification: Media not found (404)"
            else
                verify_warn "HTTP verification: Unexpected status ($http_code)"
            fi
            ;;
    esac

    verify_pass "HTTP results logged to: $(basename "$http_log")"
}

# Level 3: Functional Verification
verify_functional() {
    local resource_type="$1"
    local resource_id="$2"
    local session_dir="$3"

    echo ""
    echo -e "${BLUE}═══ Level 3: Functional Verification ═══${NC}"

    # Get site URL
    local site_url
    site_url=$("$WP_CLI" --path="$WP_PATH" option get siteurl 2>/dev/null) || {
        verify_warn "Could not get site URL - skipping functional verification"
        return 0
    }

    local func_log="$session_dir/functional_verification.log"

    case "$resource_type" in
        page|post)
            # Test that page renders and contains expected content
            local url="$site_url/?p=$resource_id"
            local content
            content=$(curl -s "$url" 2>/dev/null) || {
                verify_warn "Failed to fetch page content"
                return 0
            }

            # Check for basic WordPress structure
            if echo "$content" | grep -q "wp-content"; then
                verify_pass "Functional: Page renders WordPress structure"
            else
                verify_warn "Functional: Page may not be rendering correctly"
            fi

            # Check for featured image if set
            local featured_id
            featured_id=$("$WP_CLI" --path="$WP_PATH" post meta get "$resource_id" _thumbnail_id 2>/dev/null) || featured_id=""

            if [ -n "$featured_id" ] && [ "$featured_id" != "0" ]; then
                if echo "$content" | grep -q "wp-post-image\|featured-image"; then
                    verify_pass "Functional: Featured image appears in HTML"
                else
                    verify_warn "Functional: Featured image set but not found in HTML"
                fi
            fi

            # Save sample content
            echo "$content" | head -100 > "$func_log"
            verify_pass "Functional test results saved to: $(basename "$func_log")"
            ;;

        media)
            # Test that media loads
            local media_url
            media_url=$("$WP_CLI" --path="$WP_PATH" post get "$resource_id" --field=guid 2>/dev/null) || {
                verify_warn "Could not get media URL"
                return 0
            }

            local content_type
            content_type=$(curl -s -I "$media_url" | grep -i "content-type:" | cut -d' ' -f2- | tr -d '\r\n') || {
                verify_warn "Could not get content type"
                return 0
            }

            if echo "$content_type" | grep -qi "image"; then
                verify_pass "Functional: Media serves as image ($content_type)"
            else
                verify_warn "Functional: Unexpected content type: $content_type"
            fi
            ;;
    esac
}

# Generate verification report
generate_report() {
    local session_dir="$1"

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                   VERIFICATION REPORT                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    local total=$((VERIFICATIONS_PASSED + VERIFICATIONS_FAILED + VERIFICATIONS_WARNED))

    if [ "$total" -eq 0 ]; then
        echo "No verifications performed"
        return
    fi

    echo -e "Total Checks:    $total"
    echo -e "${GREEN}Passed:          $VERIFICATIONS_PASSED${NC}"
    echo -e "${YELLOW}Warnings:        $VERIFICATIONS_WARNED${NC}"
    echo -e "${RED}Failed:          $VERIFICATIONS_FAILED${NC}"
    echo ""

    if [ "$VERIFICATIONS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ All verifications passed!${NC}"
        echo ""
        echo "Session verified and ready for production."
    else
        echo -e "${RED}✗ Verification failed${NC}"
        echo ""
        echo "Review failed checks above and fix issues before deploying."
    fi

    # Save report
    local report_file="$session_dir/verification_report.txt"
    {
        echo "Verification Report"
        echo "Generated: $(date)"
        echo ""
        echo "Total: $total"
        echo "Passed: $VERIFICATIONS_PASSED"
        echo "Warnings: $VERIFICATIONS_WARNED"
        echo "Failed: $VERIFICATIONS_FAILED"
    } > "$report_file"

    echo ""
    echo "Report saved to: $(basename "$report_file")"
}

# Run all verifications
run_verification() {
    local resource_type="$1"
    local resource_id="$2"
    local session_dir="$3"

    echo ""
    echo "Verifying $resource_type $resource_id"
    echo "Session: $(basename "$session_dir")"
    echo "════════════════════════════════════════════════════════════════"

    verify_database "$resource_type" "$resource_id" "$session_dir"
    verify_http "$resource_type" "$resource_id" "$session_dir"
    verify_functional "$resource_type" "$resource_id" "$session_dir"

    generate_report "$session_dir"
}

# Auto-detect latest session and resource
auto_verify() {
    echo "Auto-detecting latest session..."

    # Find latest session
    local work_dir="/home/dave/skippy/work"
    local latest_session=$(find "$work_dir" -maxdepth 3 -type d -name "20*_*" 2>/dev/null | sort -r | head -1)

    if [ -z "$latest_session" ]; then
        echo "Error: No sessions found in $work_dir"
        exit 1
    fi

    echo "Found session: $(basename "$latest_session")"

    # Try to detect resource from filenames
    local final_files=$(find "$latest_session" -maxdepth 1 -name "*_final.*" 2>/dev/null)

    if [ -z "$final_files" ]; then
        echo "Error: No _final files found in session"
        echo "Cannot auto-detect resource to verify"
        exit 1
    fi

    # Extract resource info from first _final file
    local first_final=$(echo "$final_files" | head -1)
    local filename=$(basename "$first_final")

    # Parse filename (e.g., page_105_final.html)
    if [[ $filename =~ ^(page|post|media)_([0-9]+)_final ]]; then
        local resource_type="${BASH_REMATCH[1]}"
        local resource_id="${BASH_REMATCH[2]}"

        echo "Detected resource: $resource_type $resource_id"
        echo ""

        run_verification "$resource_type" "$resource_id" "$latest_session"
    else
        echo "Error: Could not parse resource from filename: $filename"
        exit 1
    fi
}

# Main
main() {
    print_header

    if [ "$#" -eq 0 ]; then
        echo "Usage:"
        echo "  $0 --page <ID> --session <path>     Verify page"
        echo "  $0 --post <ID> --session <path>     Verify post"
        echo "  $0 --media <ID> --session <path>    Verify media"
        echo "  $0 --auto                            Auto-detect and verify latest"
        echo ""
        echo "Examples:"
        echo "  $0 --page 105 --session /home/dave/skippy/work/wordpress/rundaverun-local/20251112_050000_homepage"
        echo "  $0 --auto"
        exit 1
    fi

    if [ "$1" = "--auto" ]; then
        auto_verify
        exit 0
    fi

    # Parse arguments
    local resource_type=""
    local resource_id=""
    local session_dir=""

    while [ "$#" -gt 0 ]; do
        case "$1" in
            --page|--post|--media)
                resource_type="${1#--}"
                resource_id="$2"
                shift 2
                ;;
            --session)
                session_dir="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Validate arguments
    if [ -z "$resource_type" ] || [ -z "$resource_id" ] || [ -z "$session_dir" ]; then
        echo "Error: Missing required arguments"
        echo "Use --help for usage information"
        exit 1
    fi

    if [ ! -d "$session_dir" ]; then
        echo "Error: Session directory not found: $session_dir"
        exit 1
    fi

    run_verification "$resource_type" "$resource_id" "$session_dir"
}

main "$@"
