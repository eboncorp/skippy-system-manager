#!/bin/bash

##############################################################################
# Pre-Commit Security Scan
# Version: 1.0.0
# Created: 2025-10-31
# Purpose: Scan staged files for credentials before commit
# Trigger: Anthropic API key exposure incident
#
# Usage:
#   ./pre_commit_security_scan_v1.0.0.sh           # Scan all staged files
#   ./pre_commit_security_scan_v1.0.0.sh file.txt  # Scan specific file
#
# Exit Codes:
#   0 - No credentials detected (safe to commit)
#   1 - Credentials detected (BLOCK commit)
##############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track if any issues found
ISSUES_FOUND=0

##############################################################################
# Filename Patterns to Block
##############################################################################
BLOCKED_FILENAME_PATTERNS=(
    "*api*key*"
    "*apikey*"
    "*.key"
    "*.pem"
    "*.p12"
    "*.pfx"
    "*token*"
    "*secret*"
    "*credential*"
    "*password*"
    "*.env"
    ".env.*"
    "id_rsa"
    "id_dsa"
    "id_ecdsa"
    "id_ed25519"
    "*.ppk"
    "*.crt"
    "*.cer"
    "*.der"
)

##############################################################################
# Directory Patterns to Block
##############################################################################
BLOCKED_DIRECTORIES=(
    "google_drive/Claude"
    "github/*.odt"
    "credentials/"
    "secrets/"
    ".secrets/"
    ".aws/"
    ".azure/"
    ".gcp/"
    ".anthropic/"
)

##############################################################################
# Content Patterns (API Keys, Tokens, etc.)
##############################################################################
CONTENT_PATTERNS=(
    "sk-ant-api[0-9]+-[A-Za-z0-9_-]{95,}"        # Anthropic API key
    "ghp_[a-zA-Z0-9]{36,}"                       # GitHub Personal Access Token
    "gho_[a-zA-Z0-9]{36,}"                       # GitHub OAuth token
    "github_pat_[a-zA-Z0-9_]{82,}"               # GitHub fine-grained PAT
    "AKIA[0-9A-Z]{16}"                           # AWS Access Key ID
    "AIza[0-9A-Za-z-_]{35}"                      # Google API Key
    "sk_live_[0-9a-zA-Z]{24,}"                   # Stripe Live API Key
    "sk_test_[0-9a-zA-Z]{24,}"                   # Stripe Test Key
    "sq0atp-[0-9A-Za-z\\-_]{22}"                 # Square Access Token
    "access_token[\"']\\s*:\\s*[\"'][0-9a-zA-Z]{32,}[\"']"  # OAuth token in JSON
    "api[_-]?key[\"']\\s*:\\s*[\"'][0-9a-zA-Z]{20,}[\"']"   # API key in JSON
)

##############################################################################
# Functions
##############################################################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Pre-Commit Security Scan${NC}"
    echo -e "${BLUE}  Checking for credentials and sensitive data${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_filename() {
    local file="$1"
    local basename=$(basename "$file")

    for pattern in "${BLOCKED_FILENAME_PATTERNS[@]}"; do
        # Use bash pattern matching
        if [[ "$basename" == $pattern ]]; then
            echo -e "${RED}❌ BLOCKED FILENAME:${NC} $file"
            echo -e "   ${YELLOW}Matches pattern:${NC} $pattern"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            return 1
        fi
    done

    return 0
}

check_directory() {
    local file="$1"

    for dir_pattern in "${BLOCKED_DIRECTORIES[@]}"; do
        if [[ "$file" == $dir_pattern* ]]; then
            echo -e "${RED}❌ BLOCKED DIRECTORY:${NC} $file"
            echo -e "   ${YELLOW}Matches pattern:${NC} $dir_pattern"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            return 1
        fi
    done

    return 0
}

check_file_content() {
    local file="$1"

    # Skip binary files
    if file "$file" 2>/dev/null | grep -q "binary"; then
        return 0
    fi

    # Skip if file doesn't exist or is empty
    if [[ ! -f "$file" ]] || [[ ! -s "$file" ]]; then
        return 0
    fi

    local found_pattern=0

    for pattern in "${CONTENT_PATTERNS[@]}"; do
        if grep -qE "$pattern" "$file" 2>/dev/null; then
            if [ $found_pattern -eq 0 ]; then
                echo -e "${RED}❌ CREDENTIAL DETECTED:${NC} $file"
                found_pattern=1
            fi
            echo -e "   ${YELLOW}Found pattern:${NC} $(echo $pattern | cut -c1-50)..."
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    done

    return $found_pattern
}

scan_file() {
    local file="$1"

    echo -e "${BLUE}Scanning:${NC} $file"

    # Check filename
    check_filename "$file"
    local filename_check=$?

    # Check directory
    check_directory "$file"
    local directory_check=$?

    # Check content
    check_file_content "$file"
    local content_check=$?

    # If all checks passed
    if [ $filename_check -eq 0 ] && [ $directory_check -eq 0 ] && [ $content_check -eq 0 ]; then
        echo -e "   ${GREEN}✓ Safe${NC}"
        return 0
    fi

    return 1
}

##############################################################################
# Main Execution
##############################################################################

print_header

# Determine which files to scan
if [ $# -gt 0 ]; then
    # Files specified as arguments
    FILES_TO_SCAN=("$@")
    echo "Scanning specified files: ${#FILES_TO_SCAN[@]}"
else
    # Get staged files from git
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}Error: Not in a git repository${NC}"
        exit 1
    fi

    # Get list of staged files
    mapfile -t FILES_TO_SCAN < <(git diff --cached --name-only --diff-filter=ACM)

    if [ ${#FILES_TO_SCAN[@]} -eq 0 ]; then
        echo -e "${YELLOW}No staged files to scan${NC}"
        exit 0
    fi

    echo "Scanning ${#FILES_TO_SCAN[@]} staged files"
fi

echo ""

# Scan each file
for file in "${FILES_TO_SCAN[@]}"; do
    # Skip if file doesn't exist (might be deleted)
    if [ ! -e "$file" ]; then
        continue
    fi

    scan_file "$file"
    echo ""
done

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ SCAN PASSED${NC}"
    echo -e "${GREEN}No credentials detected. Safe to commit.${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
else
    echo -e "${RED}❌ SCAN FAILED${NC}"
    echo -e "${RED}Found $ISSUES_FOUND potential credential(s) or sensitive file(s)${NC}"
    echo ""
    echo -e "${YELLOW}Actions to take:${NC}"
    echo "  1. Remove flagged files from staging:  git reset HEAD <file>"
    echo "  2. Add to .gitignore:                   echo '<pattern>' >> .gitignore"
    echo "  3. Move credentials to secure storage: ~/.secrets/ or environment variables"
    echo "  4. If false positive, override:        git commit --no-verify"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
