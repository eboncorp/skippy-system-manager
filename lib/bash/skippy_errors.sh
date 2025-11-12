#!/bin/bash
# Skippy Error Handling Library
# Version: 1.0.0
# Purpose: Centralized error handling for all Skippy scripts
# Usage: source "${SKIPPY_BASE_PATH}/lib/bash/skippy_errors.sh"

# Load logging library if not already loaded
if [[ "${SKIPPY_LOGGING_LOADED:-}" != "true" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # shellcheck source=skippy_logging.sh
    source "${SCRIPT_DIR}/skippy_logging.sh"
fi

# Error codes
readonly ERR_SUCCESS=0
readonly ERR_GENERAL=1
readonly ERR_INVALID_ARGUMENT=2
readonly ERR_FILE_NOT_FOUND=3
readonly ERR_PERMISSION_DENIED=4
readonly ERR_COMMAND_NOT_FOUND=5
readonly ERR_NETWORK_ERROR=6
readonly ERR_TIMEOUT=7
readonly ERR_DEPENDENCY_MISSING=8
readonly ERR_CONFIGURATION_ERROR=9
readonly ERR_VALIDATION_ERROR=10

readonly ERR_SYSTEM_ERROR=50
readonly ERR_DISK_FULL=51
readonly ERR_MEMORY_ERROR=52
readonly ERR_PROCESS_ERROR=53

readonly ERR_CRITICAL=100
readonly ERR_DATA_LOSS=101
readonly ERR_SECURITY_VIOLATION=102
readonly ERR_BACKUP_FAILED=103

# Global error tracking
ERROR_COUNT=0
LAST_ERROR_MESSAGE=""
LAST_ERROR_CODE=0

# Alert configuration
ALERT_EMAIL="${ALERT_EMAIL_TO:-}"
WEBHOOK_URL="${WEBHOOK_URL:-}"

#######################################
# Get error message for error code
# Arguments:
#   $1 - Error code
# Returns:
#   Error message
#######################################
get_error_message() {
    local code="$1"

    case "$code" in
        $ERR_SUCCESS) echo "Success" ;;
        $ERR_GENERAL) echo "General error" ;;
        $ERR_INVALID_ARGUMENT) echo "Invalid argument" ;;
        $ERR_FILE_NOT_FOUND) echo "File not found" ;;
        $ERR_PERMISSION_DENIED) echo "Permission denied" ;;
        $ERR_COMMAND_NOT_FOUND) echo "Command not found" ;;
        $ERR_NETWORK_ERROR) echo "Network error" ;;
        $ERR_TIMEOUT) echo "Operation timed out" ;;
        $ERR_DEPENDENCY_MISSING) echo "Required dependency missing" ;;
        $ERR_CONFIGURATION_ERROR) echo "Configuration error" ;;
        $ERR_VALIDATION_ERROR) echo "Validation error" ;;
        $ERR_SYSTEM_ERROR) echo "System error" ;;
        $ERR_DISK_FULL) echo "Disk full" ;;
        $ERR_MEMORY_ERROR) echo "Memory error" ;;
        $ERR_PROCESS_ERROR) echo "Process error" ;;
        $ERR_CRITICAL) echo "Critical error" ;;
        $ERR_DATA_LOSS) echo "Data loss detected" ;;
        $ERR_SECURITY_VIOLATION) echo "Security violation" ;;
        $ERR_BACKUP_FAILED) echo "Backup failed" ;;
        *) echo "Unknown error ($code)" ;;
    esac
}

#######################################
# Send alert for critical errors
# Arguments:
#   $1 - Severity (INFO, WARN, ERROR, CRITICAL)
#   $2 - Message
#######################################
send_alert() {
    local severity="$1"
    local message="$2"

    # Only send alerts for ERROR and CRITICAL
    if [[ "$severity" != "ERROR" ]] && [[ "$severity" != "CRITICAL" ]]; then
        return 0
    fi

    # Email alert
    if [[ -n "$ALERT_EMAIL" ]] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "Skippy Alert: $severity" "$ALERT_EMAIL" 2>/dev/null || true
    fi

    # Webhook alert
    if [[ -n "$WEBHOOK_URL" ]] && command -v curl >/dev/null 2>&1; then
        local payload
        payload=$(cat <<EOF
{
    "severity": "$severity",
    "message": "$message",
    "script": "$SCRIPT_NAME",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "hostname": "$(hostname)"
}
EOF
)
        curl -X POST -H "Content-Type: application/json" \
             -d "$payload" "$WEBHOOK_URL" \
             --max-time 5 --silent 2>/dev/null || true
    fi
}

#######################################
# Handle error and optionally exit
# Arguments:
#   $1 - Error code
#   $2 - Error message
#   $3 - Line number (optional)
#   $4 - Exit script (true/false, default: true)
#######################################
handle_error() {
    local exit_code="$1"
    local message="$2"
    local line_number="${3:-unknown}"
    local should_exit="${4:-true}"

    # Update error tracking
    ((ERROR_COUNT++))
    LAST_ERROR_CODE=$exit_code
    LAST_ERROR_MESSAGE="$message"

    # Get standard error message
    local standard_message
    standard_message=$(get_error_message "$exit_code")

    # Log error
    log_error "[$standard_message] $message (line: $line_number, code: $exit_code)"

    # Send alert for critical errors
    if ((exit_code >= ERR_CRITICAL)); then
        send_alert "CRITICAL" "[$SCRIPT_NAME] $message (line: $line_number, code: $exit_code)"
    elif ((exit_code >= ERR_SYSTEM_ERROR)); then
        send_alert "ERROR" "[$SCRIPT_NAME] $message (line: $line_number, code: $exit_code)"
    fi

    # Exit if requested
    if [[ "$should_exit" == "true" ]]; then
        exit "$exit_code"
    fi

    return "$exit_code"
}

#######################################
# Set up error trap for script
# Call this at the beginning of your script to enable automatic error handling
#######################################
setup_error_trap() {
    set -euo pipefail

    trap 'handle_error $? "Script failed" $LINENO' ERR
    trap 'handle_error $ERR_GENERAL "Script interrupted" $LINENO' INT TERM
}

#######################################
# Assert condition is true
# Arguments:
#   $1 - Condition (0 = true, non-zero = false)
#   $2 - Error message
#   $3 - Error code (optional, default: ERR_GENERAL)
#######################################
assert() {
    local condition="$1"
    local message="$2"
    local error_code="${3:-$ERR_GENERAL}"

    if ((condition != 0)); then
        handle_error "$error_code" "Assertion failed: $message" "$LINENO"
    fi
}

#######################################
# Assert command exists
# Arguments:
#   $1 - Command name
#   $2 - Error message (optional)
#######################################
assert_command_exists() {
    local command="$1"
    local message="${2:-Command not found: $command}"

    if ! command -v "$command" >/dev/null 2>&1; then
        handle_error "$ERR_COMMAND_NOT_FOUND" "$message" "$LINENO"
    fi
}

#######################################
# Assert file exists
# Arguments:
#   $1 - File path
#   $2 - Error message (optional)
#######################################
assert_file_exists() {
    local file="$1"
    local message="${2:-File not found: $file}"

    if [[ ! -f "$file" ]]; then
        handle_error "$ERR_FILE_NOT_FOUND" "$message" "$LINENO"
    fi
}

#######################################
# Assert directory exists
# Arguments:
#   $1 - Directory path
#   $2 - Error message (optional)
#######################################
assert_directory_exists() {
    local dir="$1"
    local message="${2:-Directory not found: $dir}"

    if [[ ! -d "$dir" ]]; then
        handle_error "$ERR_FILE_NOT_FOUND" "$message" "$LINENO"
    fi
}

#######################################
# Assert variable is not empty
# Arguments:
#   $1 - Variable value
#   $2 - Variable name
#######################################
assert_not_empty() {
    local value="$1"
    local name="$2"

    if [[ -z "$value" ]]; then
        handle_error "$ERR_INVALID_ARGUMENT" "Variable is empty: $name" "$LINENO"
    fi
}

#######################################
# Retry command with exponential backoff
# Arguments:
#   $1 - Command to execute
#   $2 - Max retries (optional, default: 3)
#   $3 - Initial delay in seconds (optional, default: 1)
# Returns:
#   Command exit code
#######################################
retry_command() {
    local command="$1"
    local max_retries="${2:-3}"
    local delay="${3:-1}"

    local attempt=1
    while ((attempt <= max_retries)); do
        log_debug "Attempt $attempt/$max_retries: $command"

        if eval "$command"; then
            return 0
        fi

        if ((attempt < max_retries)); then
            log_warn "Command failed, retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))  # Exponential backoff
        fi

        ((attempt++))
    done

    log_error "Command failed after $max_retries attempts: $command"
    return 1
}

#######################################
# Get error count
# Returns:
#   Number of errors encountered
#######################################
get_error_count() {
    echo "$ERROR_COUNT"
}

#######################################
# Reset error count
#######################################
reset_error_count() {
    ERROR_COUNT=0
    LAST_ERROR_MESSAGE=""
    LAST_ERROR_CODE=0
}

#######################################
# Check if script has errors
# Returns:
#   0 if no errors, 1 if errors exist
#######################################
has_errors() {
    ((ERROR_COUNT > 0))
}

# Export functions
export -f get_error_message
export -f send_alert
export -f handle_error
export -f setup_error_trap
export -f assert
export -f assert_command_exists
export -f assert_file_exists
export -f assert_directory_exists
export -f assert_not_empty
export -f retry_command
export -f get_error_count
export -f reset_error_count
export -f has_errors

# Export error codes
export ERR_SUCCESS ERR_GENERAL ERR_INVALID_ARGUMENT ERR_FILE_NOT_FOUND
export ERR_PERMISSION_DENIED ERR_COMMAND_NOT_FOUND ERR_NETWORK_ERROR
export ERR_TIMEOUT ERR_DEPENDENCY_MISSING ERR_CONFIGURATION_ERROR
export ERR_VALIDATION_ERROR ERR_SYSTEM_ERROR ERR_DISK_FULL
export ERR_MEMORY_ERROR ERR_PROCESS_ERROR ERR_CRITICAL ERR_DATA_LOSS
export ERR_SECURITY_VIOLATION ERR_BACKUP_FAILED

# Mark library as loaded
SKIPPY_ERRORS_LOADED=true
export SKIPPY_ERRORS_LOADED
