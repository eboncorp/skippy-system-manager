#!/bin/bash
# Skippy Logging Library
# Version: 1.0.0
# Purpose: Centralized logging system for all Skippy scripts
# Usage: source "${SKIPPY_BASE_PATH}/lib/bash/skippy_logging.sh"

# Color codes
readonly LOG_COLOR_RED='\033[0;31m'
readonly LOG_COLOR_GREEN='\033[0;32m'
readonly LOG_COLOR_YELLOW='\033[1;33m'
readonly LOG_COLOR_BLUE='\033[0;34m'
readonly LOG_COLOR_CYAN='\033[0;36m'
readonly LOG_COLOR_RESET='\033[0m'

# Log levels
readonly LOG_LEVEL_DEBUG=0
readonly LOG_LEVEL_INFO=1
readonly LOG_LEVEL_WARN=2
readonly LOG_LEVEL_ERROR=3
readonly LOG_LEVEL_FATAL=4

# Default log level (INFO)
LOG_LEVEL="${LOG_LEVEL:-1}"

# Log file location
LOG_FILE="${SKIPPY_LOG_FILE:-}"
LOG_TO_FILE="${SKIPPY_LOG_TO_FILE:-false}"

# Script name for logging
SCRIPT_NAME="${SCRIPT_NAME:-$(basename "$0")}"

#######################################
# Get timestamp for log entries
# Returns:
#   Formatted timestamp
#######################################
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

#######################################
# Write log entry to file
# Arguments:
#   $1 - Log level
#   $2 - Message
#######################################
write_to_log_file() {
    local level="$1"
    local message="$2"

    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        local timestamp
        timestamp=$(get_timestamp)
        echo "[$timestamp] [$level] [$SCRIPT_NAME] $message" >> "$LOG_FILE"
    fi
}

#######################################
# Log debug message
# Arguments:
#   $1 - Message
#######################################
log_debug() {
    local message="$1"

    if ((LOG_LEVEL <= LOG_LEVEL_DEBUG)); then
        echo -e "${LOG_COLOR_CYAN}[DEBUG]${LOG_COLOR_RESET} $message"
    fi

    write_to_log_file "DEBUG" "$message"
}

#######################################
# Log info message
# Arguments:
#   $1 - Message
#######################################
log_info() {
    local message="$1"

    if ((LOG_LEVEL <= LOG_LEVEL_INFO)); then
        echo -e "${LOG_COLOR_GREEN}[INFO]${LOG_COLOR_RESET} $message"
    fi

    write_to_log_file "INFO" "$message"
}

#######################################
# Log warning message
# Arguments:
#   $1 - Message
#######################################
log_warn() {
    local message="$1"

    if ((LOG_LEVEL <= LOG_LEVEL_WARN)); then
        echo -e "${LOG_COLOR_YELLOW}[WARN]${LOG_COLOR_RESET} $message" >&2
    fi

    write_to_log_file "WARN" "$message"
}

#######################################
# Log error message
# Arguments:
#   $1 - Message
#######################################
log_error() {
    local message="$1"

    if ((LOG_LEVEL <= LOG_LEVEL_ERROR)); then
        echo -e "${LOG_COLOR_RED}[ERROR]${LOG_COLOR_RESET} $message" >&2
    fi

    write_to_log_file "ERROR" "$message"
}

#######################################
# Log fatal message (same as error but more severe)
# Arguments:
#   $1 - Message
#######################################
log_fatal() {
    local message="$1"

    if ((LOG_LEVEL <= LOG_LEVEL_FATAL)); then
        echo -e "${LOG_COLOR_RED}[FATAL]${LOG_COLOR_RESET} $message" >&2
    fi

    write_to_log_file "FATAL" "$message"
}

#######################################
# Log success message (special case of info)
# Arguments:
#   $1 - Message
#######################################
log_success() {
    local message="$1"

    if ((LOG_LEVEL <= LOG_LEVEL_INFO)); then
        echo -e "${LOG_COLOR_GREEN}[✓]${LOG_COLOR_RESET} $message"
    fi

    write_to_log_file "SUCCESS" "$message"
}

#######################################
# Log with custom prefix
# Arguments:
#   $1 - Prefix
#   $2 - Message
#   $3 - Color (optional)
#######################################
log_custom() {
    local prefix="$1"
    local message="$2"
    local color="${3:-$LOG_COLOR_BLUE}"

    echo -e "${color}[$prefix]${LOG_COLOR_RESET} $message"
    write_to_log_file "$prefix" "$message"
}

#######################################
# Initialize logging system
# Arguments:
#   $1 - Log file path (optional)
#   $2 - Log level (optional: DEBUG, INFO, WARN, ERROR, FATAL)
#######################################
init_logging() {
    local log_file="$1"
    local log_level="${2:-INFO}"

    if [[ -n "$log_file" ]]; then
        LOG_FILE="$log_file"
        LOG_TO_FILE=true

        # Create log directory if it doesn't exist
        local log_dir
        log_dir=$(dirname "$log_file")
        mkdir -p "$log_dir"

        # Check if we can write to log file
        if ! touch "$log_file" 2>/dev/null; then
            echo -e "${LOG_COLOR_YELLOW}[WARN]${LOG_COLOR_RESET} Cannot write to log file: $log_file" >&2
            LOG_TO_FILE=false
        fi
    fi

    # Set log level
    case "${log_level^^}" in
        DEBUG)
            LOG_LEVEL=$LOG_LEVEL_DEBUG
            ;;
        INFO)
            LOG_LEVEL=$LOG_LEVEL_INFO
            ;;
        WARN|WARNING)
            LOG_LEVEL=$LOG_LEVEL_WARN
            ;;
        ERROR)
            LOG_LEVEL=$LOG_LEVEL_ERROR
            ;;
        FATAL)
            LOG_LEVEL=$LOG_LEVEL_FATAL
            ;;
        *)
            LOG_LEVEL=$LOG_LEVEL_INFO
            ;;
    esac
}

#######################################
# Log section header
# Arguments:
#   $1 - Section name
#######################################
log_section() {
    local section="$1"
    local separator="=================================================="

    if ((LOG_LEVEL <= LOG_LEVEL_INFO)); then
        echo ""
        echo -e "${LOG_COLOR_BLUE}$separator${LOG_COLOR_RESET}"
        echo -e "${LOG_COLOR_BLUE}  $section${LOG_COLOR_RESET}"
        echo -e "${LOG_COLOR_BLUE}$separator${LOG_COLOR_RESET}"
    fi

    write_to_log_file "SECTION" "$section"
}

#######################################
# Log progress bar
# Arguments:
#   $1 - Current value
#   $2 - Total value
#   $3 - Description (optional)
#######################################
log_progress() {
    local current="$1"
    local total="$2"
    local description="${3:-Progress}"

    local percent=$((current * 100 / total))
    local filled=$((current * 50 / total))
    local empty=$((50 - filled))

    printf "\r${description}: ["
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' ' '
    printf "] %d%%" "$percent"

    if ((current == total)); then
        echo ""
    fi
}

# Export functions
export -f get_timestamp
export -f write_to_log_file
export -f log_debug
export -f log_info
export -f log_warn
export -f log_error
export -f log_fatal
export -f log_success
export -f log_custom
export -f init_logging
export -f log_section
export -f log_progress

# Mark library as loaded
SKIPPY_LOGGING_LOADED=true
export SKIPPY_LOGGING_LOADED
