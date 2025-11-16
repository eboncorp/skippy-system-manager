#!/bin/bash
#
# WordPress Path Verification Script v1.0.0
#
# Purpose: Verify WordPress installation path before operations
# Part of: Protocol v3.0 (Step 0 verification)
# Created: November 12, 2025
#
# Prevents issues like:
# - Uploading media to wrong WordPress installation
# - Running commands against inactive site
# - Database connection failures
#
# Usage:
#   ./wp_path_verify_v1.0.0.sh [wordpress_path]
#   ./wp_path_verify_v1.0.0.sh --auto (auto-detect from Local by Flywheel)

set -e

VERSION="1.0.0"
SCRIPT_NAME="WordPress Path Verification"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  $SCRIPT_NAME v$VERSION                               ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

verify_wordpress_path() {
    local wp_path="$1"

    echo ""
    echo -e "${BLUE}═══ Verifying WordPress Installation ═══${NC}"
    echo "Path: $wp_path"
    echo ""

    # Check if directory exists
    if [ ! -d "$wp_path" ]; then
        echo -e "${RED}✗${NC} Directory does not exist: $wp_path"
        return 1
    fi
    echo -e "${GREEN}✓${NC} Directory exists"

    # Check for wp-config.php
    if [ ! -f "$wp_path/wp-config.php" ]; then
        echo -e "${RED}✗${NC} wp-config.php not found (not a WordPress installation)"
        return 1
    fi
    echo -e "${GREEN}✓${NC} wp-config.php found"

    # Check for wp-content
    if [ ! -d "$wp_path/wp-content" ]; then
        echo -e "${RED}✗${NC} wp-content directory not found"
        return 1
    fi
    echo -e "${GREEN}✓${NC} wp-content directory found"

    # Check for wp-includes
    if [ ! -d "$wp_path/wp-includes" ]; then
        echo -e "${RED}✗${NC} wp-includes directory not found"
        return 1
    fi
    echo -e "${GREEN}✓${NC} wp-includes directory found"

    # Test WP-CLI connection
    echo ""
    echo "Testing WP-CLI connection..."

    if ! command -v wp &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} WP-CLI not found in PATH"
        WP_CLI="/home/dave/skippy/bin/wp"
        if [ ! -f "$WP_CLI" ]; then
            echo -e "${RED}✗${NC} WP-CLI not available"
            return 1
        fi
    else
        WP_CLI="wp"
    fi

    # Test database connection
    if ! "$WP_CLI" --path="$wp_path" db check 2>/dev/null; then
        echo -e "${RED}✗${NC} Database connection failed"
        echo ""
        echo "Common fixes:"
        echo "  1. Check MySQL socket path in wp-config.php"
        echo "  2. Verify Local by Flywheel site is running"
        echo "  3. Check database credentials"
        return 1
    fi
    echo -e "${GREEN}✓${NC} Database connection successful"

    # Get site URL
    local site_url=$("$WP_CLI" --path="$wp_path" option get siteurl 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓${NC} Site URL: $site_url"

    # Test HTTP accessibility (if localhost)
    if [[ "$site_url" == *".local"* ]] || [[ "$site_url" == *"localhost"* ]]; then
        echo ""
        echo "Testing HTTP accessibility..."

        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$site_url" 2>/dev/null || echo "000")

        if [ "$http_code" = "200" ]; then
            echo -e "${GREEN}✓${NC} Site accessible via HTTP (200 OK)"
        else
            echo -e "${YELLOW}⚠${NC} Site returned HTTP $http_code"
            echo "  This may indicate the site is not currently served"
        fi
    fi

    # Summary
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                  VERIFICATION SUMMARY                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "Path:     ${GREEN}$wp_path${NC}"
    echo -e "URL:      ${GREEN}$site_url${NC}"
    echo -e "Status:   ${GREEN}✓ Valid WordPress Installation${NC}"
    echo ""
    echo "Safe to proceed with WordPress operations."
    echo ""

    # Export for use in scripts
    echo "export WP_PATH=\"$wp_path\""
    echo "export WP_URL=\"$site_url\""

    return 0
}

auto_detect_wordpress() {
    echo "Auto-detecting WordPress installation from Local by Flywheel..."
    echo ""

    local sites_json="$HOME/.config/Local/sites.json"

    if [ ! -f "$sites_json" ]; then
        echo -e "${RED}✗${NC} Local by Flywheel configuration not found"
        echo "  Expected: $sites_json"
        return 1
    fi

    # Extract active site path using Python
    local site_path=$(python3 <<PYEOF
import json
try:
    with open("$sites_json") as f:
        sites = json.load(f)
        # Get first site (or most recently modified)
        for site_id, site_data in sites.items():
            path = site_data.get("path", "")
            if path:
                print(f"{path}/app/public")
                break
except Exception as e:
    print("")
PYEOF
)

    if [ -z "$site_path" ]; then
        echo -e "${RED}✗${NC} Could not detect WordPress path from Local config"
        return 1
    fi

    echo "Detected path: $site_path"
    verify_wordpress_path "$site_path"
}

# Main
main() {
    print_header

    if [ "$#" -eq 0 ]; then
        echo "Usage:"
        echo "  $0 /path/to/wordpress     Verify specific WordPress path"
        echo "  $0 --auto                 Auto-detect from Local by Flywheel"
        echo ""
        echo "Examples:"
        echo "  $0 /home/dave/skippy/rundaverun_local_site/app/public"
        echo "  $0 --auto"
        exit 1
    fi

    case "$1" in
        --auto)
            auto_detect_wordpress
            ;;
        *)
            verify_wordpress_path "$1"
            ;;
    esac
}

main "$@"
