#!/bin/bash
# Configuration Validation Script
# Version: 1.0.0
# Purpose: Validate that all required environment variables are set
# Usage: source config.env && bash scripts/utility/validate_config.sh

set -euo pipefail

echo "===================================="
echo "  Configuration Validation"
echo "  Version: 1.0.0"
echo "===================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to check if variable is set and not empty
check_required() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [ -z "$var_value" ] || [ "$var_value" = "<"* ]; then
        echo -e "${RED}✗ ERROR: ${var_name} is not set or using placeholder value${NC}"
        ((ERRORS++))
        return 1
    else
        echo -e "${GREEN}✓ ${var_name}${NC}"
        return 0
    fi
}

# Function to check optional variable
check_optional() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [ -z "$var_value" ] || [ "$var_value" = "<"* ]; then
        echo -e "${YELLOW}⚠ WARNING: ${var_name} is not set (optional)${NC}"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ ${var_name}${NC}"
    fi
}

# Function to check if path exists
check_path() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [ -n "$var_value" ] && [ "$var_value" != "<"* ]; then
        if [ -d "$var_value" ]; then
            echo -e "${GREEN}✓ ${var_name} exists: ${var_value}${NC}"
        else
            echo -e "${YELLOW}⚠ WARNING: ${var_name} path does not exist: ${var_value}${NC}"
            ((WARNINGS++))
        fi
    fi
}

echo "Checking required base paths..."
check_required "SKIPPY_BASE_PATH"
check_required "WORDPRESS_BASE_PATH"
check_path "SKIPPY_BASE_PATH"
check_path "WORDPRESS_BASE_PATH"
echo ""

echo "Checking remote server configuration..."
check_required "EBON_HOST"
check_required "EBON_PASSWORD"
echo ""

echo "Checking WordPress configuration..."
check_required "WP_SITE_URL"
check_optional "WP_ADMIN_USER"
check_optional "WP_ADMIN_PASSWORD"
check_optional "WP_DB_NAME"
check_optional "WP_DB_USER"
check_optional "WP_DB_PASSWORD"
echo ""

echo "Checking cloud storage configuration..."
check_optional "GDRIVE_CLIENT_ID"
check_optional "GDRIVE_CLIENT_SECRET"
check_optional "GDRIVE_REFRESH_TOKEN"
echo ""

echo "Checking GitHub configuration..."
check_optional "GITHUB_REPO_OWNER"
check_optional "GITHUB_REPO_NAME"
check_optional "GITHUB_TOKEN"
echo ""

echo "Checking email/notification configuration..."
check_optional "SMTP_HOST"
check_optional "ALERT_EMAIL_TO"
echo ""

echo "===================================="
echo "  Validation Summary"
echo "===================================="
echo -e "Errors: ${RED}${ERRORS}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Configuration validation FAILED!${NC}"
    echo "Please fix the errors above before running scripts."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Configuration validation passed with warnings.${NC}"
    echo "Some optional features may not work without the missing variables."
    exit 0
else
    echo -e "${GREEN}Configuration validation PASSED!${NC}"
    echo "All required variables are set correctly."
    exit 0
fi
