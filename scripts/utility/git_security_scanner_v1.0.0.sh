#!/bin/bash
#
# Git Repository Security Scanner v1.0.0
#
# Purpose: Scans git repositories for sensitive files and security issues
# Part of: Protocol v3.1 (Git Security Enhancement)
# Created: November 12, 2025
#
# Prevents issues like:
# - SQL files committed to repository (database exposure)
# - wp-config.php tracked (credential exposure)
# - .env files committed (API key exposure)
# - Private keys in version control
#
# Usage:
#   ./git_security_scanner_v1.0.0.sh [repository_path]
#   ./git_security_scanner_v1.0.0.sh --all (scan all repositories in ~/skippy/)
#   ./git_security_scanner_v1.0.0.sh --fix (attempt auto-fix by removing from git)

set -e

VERSION="1.0.0"
SCRIPT_NAME="Git Security Scanner"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
CRITICAL_ISSUES=0
HIGH_ISSUES=0
MEDIUM_ISSUES=0
LOW_ISSUES=0

# Sensitive file patterns
CRITICAL_PATTERNS=(
    "*.sql"              # Database dumps
    "wp-config.php"      # WordPress config
    "*.pem"              # Private keys
    "*.key"              # Private keys
    "id_rsa"             # SSH private key
    "id_dsa"             # SSH private key
    "id_ecdsa"           # SSH private key
    "id_ed25519"         # SSH private key
)

HIGH_PATTERNS=(
    ".env"               # Environment variables
    ".env.*"             # Environment variants
    "credentials.json"   # API credentials
    "*.p12"              # Certificate files
    "*.pfx"              # Certificate files
)

MEDIUM_PATTERNS=(
    "*password*"         # Files with password in name
    "*secret*"           # Files with secret in name
    "*token*"            # Files with token in name
)

print_header() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  $SCRIPT_NAME v$VERSION                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

issue_critical() {
    ((CRITICAL_ISSUES++))
    echo -e "${RED}🔴 CRITICAL:${NC} $1"
}

issue_high() {
    ((HIGH_ISSUES++))
    echo -e "${YELLOW}🟠 HIGH:${NC} $1"
}

issue_medium() {
    ((MEDIUM_ISSUES++))
    echo -e "${YELLOW}🟡 MEDIUM:${NC} $1"
}

issue_low() {
    ((LOW_ISSUES++))
    echo -e "${BLUE}🔵 LOW:${NC} $1"
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

# Scan repository for sensitive files
scan_repository() {
    local repo_path="$1"
    local fix_mode="$2"

    echo ""
    echo -e "${BLUE}═══ Scanning Repository ═══${NC}"
    echo "Path: $repo_path"
    echo ""

    # Check if it's a git repository
    if [ ! -d "$repo_path/.git" ]; then
        echo -e "${YELLOW}⚠${NC} Not a git repository: $repo_path"
        return 1
    fi

    cd "$repo_path" || return 1

    # Check for .gitignore
    if [ ! -f ".gitignore" ]; then
        issue_medium ".gitignore file missing"
    else
        check_pass ".gitignore file exists"
    fi

    # Scan for critical files
    echo ""
    echo -e "${RED}Checking for CRITICAL files:${NC}"

    local found_critical=false
    for pattern in "${CRITICAL_PATTERNS[@]}"; do
        local files=$(git ls-files | grep -E "^${pattern//\*/.*}$" || true)
        if [ -n "$files" ]; then
            found_critical=true
            while IFS= read -r file; do
                issue_critical "Tracked in git: $file"

                if [ "$fix_mode" = "true" ]; then
                    echo "  → Removing from git: $file"
                    git rm --cached "$file" 2>/dev/null || true
                fi
            done <<< "$files"
        fi
    done

    if [ "$found_critical" = "false" ]; then
        check_pass "No critical files found in git"
    fi

    # Scan for high-risk files
    echo ""
    echo -e "${YELLOW}Checking for HIGH-RISK files:${NC}"

    local found_high=false
    for pattern in "${HIGH_PATTERNS[@]}"; do
        local files=$(git ls-files | grep -E "^${pattern//\*/.*}$" || true)
        if [ -n "$files" ]; then
            found_high=true
            while IFS= read -r file; do
                issue_high "Tracked in git: $file"

                if [ "$fix_mode" = "true" ]; then
                    echo "  → Removing from git: $file"
                    git rm --cached "$file" 2>/dev/null || true
                fi
            done <<< "$files"
        fi
    done

    if [ "$found_high" = "false" ]; then
        check_pass "No high-risk files found in git"
    fi

    # Check .gitignore coverage
    echo ""
    echo -e "${BLUE}Checking .gitignore coverage:${NC}"

    if [ -f ".gitignore" ]; then
        # Check if critical patterns are in .gitignore
        local missing_patterns=()

        for pattern in "${CRITICAL_PATTERNS[@]}"; do
            if ! grep -q "^${pattern}$" .gitignore 2>/dev/null && ! grep -q "^${pattern//\*/\\\*}$" .gitignore 2>/dev/null; then
                missing_patterns+=("$pattern")
            fi
        done

        if [ ${#missing_patterns[@]} -gt 0 ]; then
            issue_medium ".gitignore missing critical patterns: ${missing_patterns[*]}"

            if [ "$fix_mode" = "true" ]; then
                echo "  → Adding patterns to .gitignore"
                for pattern in "${missing_patterns[@]}"; do
                    echo "$pattern" >> .gitignore
                done
            fi
        else
            check_pass ".gitignore covers critical file types"
        fi
    fi

    # Check for large files (might be database dumps)
    echo ""
    echo -e "${BLUE}Checking for large files (>1MB):${NC}"

    local large_files=$(git ls-files | xargs -I {} sh -c 'test -f "{}" && du -m "{}" | awk "\$1 > 1"' 2>/dev/null || true)

    if [ -n "$large_files" ]; then
        while IFS= read -r line; do
            local size=$(echo "$line" | awk '{print $1}')
            local file=$(echo "$line" | awk '{print $2}')
            issue_low "Large file in git (${size}MB): $file"
        done <<< "$large_files"
    else
        check_pass "No large files detected"
    fi

    # Check for wp-config.php specifically
    echo ""
    echo -e "${RED}WordPress Security Check:${NC}"

    if git ls-files | grep -q "wp-config\.php"; then
        issue_critical "wp-config.php is tracked in git (credential exposure risk)"

        if [ "$fix_mode" = "true" ]; then
            echo "  → Removing wp-config.php from git"
            git rm --cached wp-config.php 2>/dev/null || true
            echo "wp-config.php" >> .gitignore
        fi
    else
        check_pass "wp-config.php not tracked in git"
    fi

    # Generate report
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                      SECURITY REPORT                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    local total=$((CRITICAL_ISSUES + HIGH_ISSUES + MEDIUM_ISSUES + LOW_ISSUES))

    echo "Total Issues: $total"
    echo -e "${RED}Critical:     $CRITICAL_ISSUES${NC}"
    echo -e "${YELLOW}High:         $HIGH_ISSUES${NC}"
    echo -e "${YELLOW}Medium:       $MEDIUM_ISSUES${NC}"
    echo -e "${BLUE}Low:          $LOW_ISSUES${NC}"
    echo ""

    if [ "$CRITICAL_ISSUES" -gt 0 ]; then
        echo -e "${RED}⚠ CRITICAL ISSUES FOUND${NC}"
        echo "Run with --fix to automatically remove sensitive files from git"
        echo ""
        echo "Manual fix steps:"
        echo "  1. git rm --cached <file>"
        echo "  2. Add pattern to .gitignore"
        echo "  3. git commit -m 'SECURITY: Remove sensitive files'"
        echo "  4. IMPORTANT: Rotate all exposed credentials"
        return 1
    elif [ "$HIGH_ISSUES" -gt 0 ]; then
        echo -e "${YELLOW}⚠ HIGH-RISK ISSUES FOUND${NC}"
        echo "Address these issues before pushing to remote"
        return 1
    elif [ "$MEDIUM_ISSUES" -gt 0 ]; then
        echo -e "${YELLOW}⚠ MEDIUM-RISK ISSUES FOUND${NC}"
        echo "Consider addressing these issues"
    else
        echo -e "${GREEN}✓ No security issues detected${NC}"
        echo "Repository is safe for version control"
    fi

    return 0
}

# Scan all repositories
scan_all_repositories() {
    echo "Scanning all repositories in /home/dave/skippy..."
    echo ""

    local repos=$(find /home/dave/skippy -name ".git" -type d 2>/dev/null | sed 's|/.git||')

    if [ -z "$repos" ]; then
        echo "No git repositories found"
        return 1
    fi

    local repo_count=$(echo "$repos" | wc -l)
    echo "Found $repo_count repositories"
    echo ""

    local current=1
    while IFS= read -r repo; do
        echo "════════════════════════════════════════════════════════════════"
        echo "Repository $current of $repo_count: $(basename "$repo")"
        echo "════════════════════════════════════════════════════════════════"

        # Reset counters for each repo
        CRITICAL_ISSUES=0
        HIGH_ISSUES=0
        MEDIUM_ISSUES=0
        LOW_ISSUES=0

        scan_repository "$repo" "false"

        echo ""
        ((current++))
    done <<< "$repos"
}

# Main
main() {
    print_header

    if [ "$#" -eq 0 ]; then
        echo "Usage:"
        echo "  $0 /path/to/repository        Scan specific repository"
        echo "  $0 --all                      Scan all repositories in ~/skippy/"
        echo "  $0 --fix /path/to/repository  Scan and auto-fix issues"
        echo ""
        echo "Examples:"
        echo "  $0 /home/dave/rundaverun"
        echo "  $0 --all"
        echo "  $0 --fix /home/dave/rundaverun"
        exit 1
    fi

    case "$1" in
        --all)
            scan_all_repositories
            ;;
        --fix)
            if [ -z "$2" ]; then
                echo "Error: --fix requires repository path"
                exit 1
            fi
            scan_repository "$2" "true"
            ;;
        *)
            scan_repository "$1" "false"
            ;;
    esac
}

main "$@"
