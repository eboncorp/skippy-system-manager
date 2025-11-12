#!/bin/bash
# Skippy Input Validation Library
# Version: 1.0.0
# Purpose: Centralized input validation to prevent security vulnerabilities
# Usage: source "${SKIPPY_BASE_PATH}/lib/bash/skippy_validation.sh"

# Color codes for output
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_RESET='\033[0m'

# Validation error flag
VALIDATION_ERRORS=0

#######################################
# Log validation error
# Arguments:
#   $1 - Error message
#######################################
log_validation_error() {
    local message="$1"
    echo -e "${COLOR_RED}[VALIDATION ERROR]${COLOR_RESET} $message" >&2
    ((VALIDATION_ERRORS++))
}

#######################################
# Log validation warning
# Arguments:
#   $1 - Warning message
#######################################
log_validation_warning() {
    local message="$1"
    echo -e "${COLOR_YELLOW}[VALIDATION WARNING]${COLOR_RESET} $message" >&2
}

#######################################
# Validate and sanitize file path
# Arguments:
#   $1 - Path to validate
# Returns:
#   0 if valid, 1 if invalid
# Outputs:
#   Sanitized path to stdout
#######################################
validate_path() {
    local path="$1"

    if [[ -z "$path" ]]; then
        log_validation_error "Path is empty"
        return 1
    fi

    # Check for path traversal attempts
    if [[ "$path" == *".."* ]]; then
        log_validation_error "Path traversal detected: $path"
        return 1
    fi

    # Check for null bytes
    if [[ "$path" == *$'\0'* ]]; then
        log_validation_error "Null byte detected in path: $path"
        return 1
    fi

    # Remove dangerous characters but keep valid path characters
    local sanitized
    sanitized=$(echo "$path" | tr -cd '[:alnum:]._/-')

    if [[ "$sanitized" != "$path" ]]; then
        log_validation_warning "Path contained invalid characters, sanitized to: $sanitized"
    fi

    echo "$sanitized"
    return 0
}

#######################################
# Validate filename (no directory separators)
# Arguments:
#   $1 - Filename to validate
# Returns:
#   0 if valid, 1 if invalid
# Outputs:
#   Sanitized filename to stdout
#######################################
validate_filename() {
    local filename="$1"

    if [[ -z "$filename" ]]; then
        log_validation_error "Filename is empty"
        return 1
    fi

    # Check for directory separators
    if [[ "$filename" == *"/"* ]]; then
        log_validation_error "Filename contains directory separator: $filename"
        return 1
    fi

    # Only allow alphanumeric, dots, dashes, underscores
    if [[ ! "$filename" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        log_validation_error "Filename contains invalid characters: $filename"
        return 1
    fi

    # Prevent hidden files unless explicitly allowed
    if [[ "$filename" == .* ]] && [[ "$ALLOW_HIDDEN_FILES" != "true" ]]; then
        log_validation_warning "Hidden filename detected: $filename"
    fi

    echo "$filename"
    return 0
}

#######################################
# Validate URL
# Arguments:
#   $1 - URL to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_url() {
    local url="$1"

    if [[ -z "$url" ]]; then
        log_validation_error "URL is empty"
        return 1
    fi

    # Check for valid URL pattern (http/https)
    if [[ ! "$url" =~ ^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$ ]]; then
        log_validation_error "Invalid URL format: $url"
        return 1
    fi

    echo "$url"
    return 0
}

#######################################
# Validate email address
# Arguments:
#   $1 - Email to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_email() {
    local email="$1"

    if [[ -z "$email" ]]; then
        log_validation_error "Email is empty"
        return 1
    fi

    # Basic email validation
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_validation_error "Invalid email format: $email"
        return 1
    fi

    echo "$email"
    return 0
}

#######################################
# Validate IP address (IPv4)
# Arguments:
#   $1 - IP address to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_ip() {
    local ip="$1"

    if [[ -z "$ip" ]]; then
        log_validation_error "IP address is empty"
        return 1
    fi

    # Validate IPv4 format
    if [[ ! "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        log_validation_error "Invalid IP format: $ip"
        return 1
    fi

    # Validate each octet
    local IFS='.'
    local -a octets=($ip)
    for octet in "${octets[@]}"; do
        if ((octet > 255)); then
            log_validation_error "IP octet out of range: $ip"
            return 1
        fi
    done

    echo "$ip"
    return 0
}

#######################################
# Validate port number
# Arguments:
#   $1 - Port number to validate
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_port() {
    local port="$1"

    if [[ -z "$port" ]]; then
        log_validation_error "Port is empty"
        return 1
    fi

    # Check if numeric
    if [[ ! "$port" =~ ^[0-9]+$ ]]; then
        log_validation_error "Port must be numeric: $port"
        return 1
    fi

    # Check range
    if ((port < 1 || port > 65535)); then
        log_validation_error "Port out of range (1-65535): $port"
        return 1
    fi

    echo "$port"
    return 0
}

#######################################
# Validate alphanumeric string
# Arguments:
#   $1 - String to validate
#   $2 - Allow spaces (optional, default: false)
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_alphanumeric() {
    local string="$1"
    local allow_spaces="${2:-false}"

    if [[ -z "$string" ]]; then
        log_validation_error "String is empty"
        return 1
    fi

    if [[ "$allow_spaces" == "true" ]]; then
        if [[ ! "$string" =~ ^[a-zA-Z0-9\ ]+$ ]]; then
            log_validation_error "String contains non-alphanumeric characters: $string"
            return 1
        fi
    else
        if [[ ! "$string" =~ ^[a-zA-Z0-9]+$ ]]; then
            log_validation_error "String contains non-alphanumeric characters: $string"
            return 1
        fi
    fi

    echo "$string"
    return 0
}

#######################################
# Validate integer
# Arguments:
#   $1 - Value to validate
#   $2 - Minimum value (optional)
#   $3 - Maximum value (optional)
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_integer() {
    local value="$1"
    local min="${2:-}"
    local max="${3:-}"

    if [[ -z "$value" ]]; then
        log_validation_error "Value is empty"
        return 1
    fi

    # Check if integer
    if [[ ! "$value" =~ ^-?[0-9]+$ ]]; then
        log_validation_error "Value is not an integer: $value"
        return 1
    fi

    # Check minimum
    if [[ -n "$min" ]] && ((value < min)); then
        log_validation_error "Value $value is less than minimum $min"
        return 1
    fi

    # Check maximum
    if [[ -n "$max" ]] && ((value > max)); then
        log_validation_error "Value $value is greater than maximum $max"
        return 1
    fi

    echo "$value"
    return 0
}

#######################################
# Validate boolean value
# Arguments:
#   $1 - Value to validate
# Returns:
#   0 if valid (outputs "true" or "false"), 1 if invalid
#######################################
validate_boolean() {
    local value="$1"

    if [[ -z "$value" ]]; then
        log_validation_error "Boolean value is empty"
        return 1
    fi

    case "${value,,}" in
        true|yes|1|on)
            echo "true"
            return 0
            ;;
        false|no|0|off)
            echo "false"
            return 0
            ;;
        *)
            log_validation_error "Invalid boolean value: $value"
            return 1
            ;;
    esac
}

#######################################
# Sanitize SQL input (basic protection)
# Arguments:
#   $1 - String to sanitize
# Returns:
#   Sanitized string to stdout
#######################################
sanitize_sql() {
    local input="$1"

    # Remove dangerous SQL keywords and characters
    local sanitized
    sanitized=$(echo "$input" | sed 's/[;]//g' | sed "s/['\"\\]//g")

    if [[ "$sanitized" != "$input" ]]; then
        log_validation_warning "SQL input contained dangerous characters, sanitized"
    fi

    echo "$sanitized"
}

#######################################
# Check if file exists and is readable
# Arguments:
#   $1 - File path
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_file_exists() {
    local file="$1"

    if [[ -z "$file" ]]; then
        log_validation_error "File path is empty"
        return 1
    fi

    if [[ ! -f "$file" ]]; then
        log_validation_error "File does not exist: $file"
        return 1
    fi

    if [[ ! -r "$file" ]]; then
        log_validation_error "File is not readable: $file"
        return 1
    fi

    return 0
}

#######################################
# Check if directory exists and is accessible
# Arguments:
#   $1 - Directory path
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_directory_exists() {
    local dir="$1"

    if [[ -z "$dir" ]]; then
        log_validation_error "Directory path is empty"
        return 1
    fi

    if [[ ! -d "$dir" ]]; then
        log_validation_error "Directory does not exist: $dir"
        return 1
    fi

    if [[ ! -r "$dir" ]] || [[ ! -x "$dir" ]]; then
        log_validation_error "Directory is not accessible: $dir"
        return 1
    fi

    return 0
}

#######################################
# Reset validation error counter
#######################################
reset_validation_errors() {
    VALIDATION_ERRORS=0
}

#######################################
# Get validation error count
# Returns:
#   Number of validation errors
#######################################
get_validation_errors() {
    echo "$VALIDATION_ERRORS"
}

# Export functions for use in other scripts
export -f log_validation_error
export -f log_validation_warning
export -f validate_path
export -f validate_filename
export -f validate_url
export -f validate_email
export -f validate_ip
export -f validate_port
export -f validate_alphanumeric
export -f validate_integer
export -f validate_boolean
export -f sanitize_sql
export -f validate_file_exists
export -f validate_directory_exists
export -f reset_validation_errors
export -f get_validation_errors

# Mark library as loaded
SKIPPY_VALIDATION_LOADED=true
export SKIPPY_VALIDATION_LOADED
