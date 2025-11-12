#!/bin/bash
# Configuration Validation Tool v2.0.0
# Purpose: Validate Skippy configuration before running scripts
# Usage: ./validate_config_v2.0.0.sh

set -euo pipefail

# Colors
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# Counters
ERRORS=0
WARNINGS=0
INFO_COUNT=0

#######################################
# Print colored message
#######################################
print_colored() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${COLOR_RESET}"
}

#######################################
# Log error
#######################################
log_error() {
    local message="$1"
    print_colored "$COLOR_RED" "❌ ERROR: $message"
    ((ERRORS++))
}

#######################################
# Log warning
#######################################
log_warning() {
    local message="$1"
    print_colored "$COLOR_YELLOW" "⚠️  WARNING: $message"
    ((WARNINGS++))
}

#######################################
# Log success
#######################################
log_success() {
    local message="$1"
    print_colored "$COLOR_GREEN" "✓ $message"
}

#######################################
# Log info
#######################################
log_info() {
    local message="$1"
    print_colored "$COLOR_BLUE" "ℹ️  $message"
    ((INFO_COUNT++))
}

#######################################
# Check if variable is set and not empty
#######################################
check_required_var() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [[ -z "$var_value" ]]; then
        log_error "Required variable not set: $var_name"
        return 1
    fi

    log_success "$var_name is set"
    return 0
}

#######################################
# Check if directory exists
#######################################
check_directory() {
    local var_name="$1"
    local dir_path="${!var_name:-}"

    if [[ -z "$dir_path" ]]; then
        log_warning "$var_name not set"
        return 1
    fi

    if [[ ! -d "$dir_path" ]]; then
        log_warning "Directory does not exist: $dir_path ($var_name)"
        log_info "You may need to create it: mkdir -p $dir_path"
        return 1
    fi

    if [[ ! -r "$dir_path" ]] || [[ ! -x "$dir_path" ]]; then
        log_error "Directory not accessible: $dir_path ($var_name)"
        return 1
    fi

    log_success "$var_name directory exists and is accessible"
    return 0
}

#######################################
# Check if command exists
#######################################
check_command() {
    local command="$1"
    local required="${2:-false}"

    if command -v "$command" >/dev/null 2>&1; then
        log_success "Command available: $command"
        return 0
    else
        if [[ "$required" == "true" ]]; then
            log_error "Required command not found: $command"
        else
            log_warning "Optional command not found: $command"
        fi
        return 1
    fi
}

#######################################
# Validate SSH connection
#######################################
validate_ssh() {
    local host="${EBON_HOST:-}"

    if [[ -z "$host" ]]; then
        log_warning "EBON_HOST not set, skipping SSH validation"
        return 0
    fi

    log_info "Validating SSH connection to $host..."

    if timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=5 \
       -o StrictHostKeyChecking=no "$host" exit 2>/dev/null; then
        log_success "SSH connection successful"
        return 0
    else
        log_warning "SSH connection failed (may require password or key setup)"
        return 1
    fi
}

#######################################
# Main validation
#######################################
main() {
    print_colored "$COLOR_BLUE" "=================================================="
    print_colored "$COLOR_BLUE" "  Skippy Configuration Validation"
    print_colored "$COLOR_BLUE" "=================================================="
    echo ""

    # Check if config.env exists
    local config_file="${SKIPPY_BASE_PATH:-}/config.env"
    if [[ -z "${SKIPPY_BASE_PATH:-}" ]]; then
        config_file="./config.env"
    fi

    if [[ -f "$config_file" ]]; then
        log_success "Found config.env at: $config_file"
        # shellcheck disable=SC1090
        source "$config_file"
    else
        log_warning "config.env not found at: $config_file"
        log_info "Using environment variables or defaults"
    fi

    echo ""
    print_colored "$COLOR_BLUE" "=== Required Variables ==="
    check_required_var "SKIPPY_BASE_PATH" || true
    check_required_var "WORDPRESS_BASE_PATH" || true

    echo ""
    print_colored "$COLOR_BLUE" "=== Directory Validation ==="
    check_directory "SKIPPY_BASE_PATH" || true
    check_directory "WORDPRESS_BASE_PATH" || true

    echo ""
    print_colored "$COLOR_BLUE" "=== Required Commands ==="
    check_command "bash" "true"
    check_command "python3" "true"
    check_command "git" "true"

    echo ""
    print_colored "$COLOR_BLUE" "=== Optional Commands ==="
    check_command "wp" "false" || true
    check_command "ssh" "false" || true
    check_command "curl" "false" || true
    check_command "jq" "false" || true
    check_command "gpg" "false" || true

    echo ""
    print_colored "$COLOR_BLUE" "=== Remote Server ==="
    if [[ -n "${EBON_HOST:-}" ]]; then
        log_info "EBON_HOST: $EBON_HOST"
        validate_ssh || true
    else
        log_warning "EBON_HOST not configured"
    fi

    echo ""
    print_colored "$COLOR_BLUE" "=== WordPress Configuration ==="
    if [[ -n "${WP_SITE_URL:-}" ]]; then
        log_info "WP_SITE_URL: $WP_SITE_URL"
    else
        log_warning "WP_SITE_URL not set"
    fi

    echo ""
    print_colored "$COLOR_BLUE" "=================================================="
    print_colored "$COLOR_BLUE" "  Validation Summary"
    print_colored "$COLOR_BLUE" "=================================================="
    echo ""
    echo "Errors:   $ERRORS"
    echo "Warnings: $WARNINGS"
    echo "Info:     $INFO_COUNT"
    echo ""

    if ((ERRORS > 0)); then
        print_colored "$COLOR_RED" "❌ Configuration validation FAILED"
        print_colored "$COLOR_YELLOW" "Please fix the errors above before running Skippy scripts"
        exit 1
    elif ((WARNINGS > 0)); then
        print_colored "$COLOR_YELLOW" "⚠️  Configuration validation passed with warnings"
        print_colored "$COLOR_YELLOW" "Some optional features may not work correctly"
        exit 0
    else
        print_colored "$COLOR_GREEN" "✅ Configuration validation PASSED"
        print_colored "$COLOR_GREEN" "All systems ready!"
        exit 0
    fi
}

main
