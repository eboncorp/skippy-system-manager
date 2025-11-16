#!/usr/bin/env bash
#
# Skippy System Manager - Robust Bash Script Template
# Version: 1.0.0
# Created: 2025-11-16
#
# This template provides a foundation for robust bash scripts with:
# - Strict error handling (set -euo pipefail)
# - Comprehensive logging
# - Graceful cleanup on exit
# - Error reporting
# - Configuration validation
# - Retry logic for operations
# - Lock file support for single-instance execution
#
# Usage:
#   1. Copy this template to your new script
#   2. Modify SCRIPT_NAME, SCRIPT_VERSION, and SCRIPT_DESCRIPTION
#   3. Implement your logic in the main() function
#   4. Add any custom functions as needed
#

# =============================================================================
# STRICT MODE - Fail fast on errors
# =============================================================================
set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# SCRIPT METADATA
# =============================================================================
readonly SCRIPT_NAME="robust_template"
readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DESCRIPTION="Robust bash script template with error handling"
readonly SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_FILE="$(basename "${BASH_SOURCE[0]}")"

# =============================================================================
# CONFIGURATION
# =============================================================================
# Load from environment or use defaults
SKIPPY_BASE_PATH="${SKIPPY_BASE_PATH:-/home/dave/skippy}"
LOG_DIR="${SKIPPY_BASE_PATH}/logs"
LOG_FILE="${LOG_DIR}/${SCRIPT_NAME}.log"
LOCK_FILE="/tmp/${SCRIPT_NAME}.lock"
MAX_LOG_SIZE_MB=10
LOG_RETENTION_DAYS=30

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=2
RETRY_BACKOFF_MULTIPLIER=2

# Feature flags
ENABLE_LOCK_FILE=true
ENABLE_LOGGING=true
DRY_RUN=false
VERBOSE=false

# =============================================================================
# COLOR OUTPUT (if terminal supports it)
# =============================================================================
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly CYAN='\033[0;36m'
    readonly NC='\033[0m' # No Color
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly CYAN=''
    readonly NC=''
fi

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

# Ensure log directory exists
setup_logging() {
    if [[ "$ENABLE_LOGGING" == "true" ]]; then
        mkdir -p "$LOG_DIR"

        # Rotate log if too large
        if [[ -f "$LOG_FILE" ]]; then
            local size_mb
            size_mb=$(du -m "$LOG_FILE" 2>/dev/null | cut -f1)
            if [[ "$size_mb" -ge "$MAX_LOG_SIZE_MB" ]]; then
                mv "$LOG_FILE" "${LOG_FILE}.$(date +%Y%m%d_%H%M%S).bak"
                log_info "Log file rotated due to size"
            fi
        fi
    fi
}

# Log message to file and optionally console
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entry="[$timestamp] [$level] [$SCRIPT_NAME] $message"

    if [[ "$ENABLE_LOGGING" == "true" ]]; then
        echo "$log_entry" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

log_info() {
    log "INFO" "$@"
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${GREEN}[INFO]${NC} $*" >&2
    fi
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        log "DEBUG" "$@"
        echo -e "${CYAN}[DEBUG]${NC} $*" >&2
    fi
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

# =============================================================================
# ERROR HANDLING
# =============================================================================

# Trap for cleanup on exit
cleanup() {
    local exit_code=$?

    log_debug "Cleanup triggered with exit code: $exit_code"

    # Remove lock file if we created it
    if [[ "$ENABLE_LOCK_FILE" == "true" && -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log_debug "Lock file removed"
    fi

    # Add any additional cleanup here
    # e.g., remove temporary files, close connections, etc.

    if [[ $exit_code -ne 0 ]]; then
        log_error "Script exited with code $exit_code"
    else
        log_info "Script completed successfully"
    fi

    exit $exit_code
}

# Error handler for specific line
error_handler() {
    local line_number=$1
    local error_code=$2
    local command="$3"

    log_error "Error on line $line_number: Command '$command' exited with code $error_code"

    # Send notification if configured
    # notify_error "$SCRIPT_NAME" "Error on line $line_number"
}

# Set up traps
trap cleanup EXIT
trap 'error_handler ${LINENO} $? "${BASH_COMMAND}"' ERR

# =============================================================================
# LOCK FILE MANAGEMENT
# =============================================================================

acquire_lock() {
    if [[ "$ENABLE_LOCK_FILE" != "true" ]]; then
        return 0
    fi

    if [[ -f "$LOCK_FILE" ]]; then
        local pid
        pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")

        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            log_error "Script is already running with PID $pid"
            exit 1
        else
            log_warn "Stale lock file found, removing"
            rm -f "$LOCK_FILE"
        fi
    fi

    echo $$ > "$LOCK_FILE"
    log_debug "Lock acquired (PID: $$)"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Validate required environment variables
validate_environment() {
    local missing_vars=()

    # Add required variables here
    # local required_vars=("VAR1" "VAR2")
    local required_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi

    return 0
}

# Validate required commands are available
validate_commands() {
    local missing_cmds=()

    # Add required commands here
    local required_cmds=("date" "mkdir" "rm")

    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_cmds+=("$cmd")
        fi
    done

    if [[ ${#missing_cmds[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing_cmds[*]}"
        return 1
    fi

    return 0
}

# Validate paths exist
validate_paths() {
    local paths_to_check=("$SKIPPY_BASE_PATH")

    for path in "${paths_to_check[@]}"; do
        if [[ ! -d "$path" ]]; then
            log_error "Required directory does not exist: $path"
            return 1
        fi
    done

    return 0
}

# =============================================================================
# RETRY LOGIC
# =============================================================================

# Execute command with retry logic and exponential backoff
retry() {
    local max_attempts="$MAX_RETRIES"
    local delay="$RETRY_DELAY"
    local attempt=1
    local exit_code=0

    while [[ $attempt -le $max_attempts ]]; do
        log_debug "Attempt $attempt/$max_attempts: $*"

        set +e
        "$@"
        exit_code=$?
        set -e

        if [[ $exit_code -eq 0 ]]; then
            return 0
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Attempt $attempt failed (exit code: $exit_code). Retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * RETRY_BACKOFF_MULTIPLIER))
        fi

        attempt=$((attempt + 1))
    done

    log_error "Command failed after $max_attempts attempts: $*"
    return $exit_code
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Check if script is running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Check if script is NOT running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Get confirmation from user
confirm() {
    local message="${1:-Continue?}"
    local response

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would prompt: $message"
        return 0
    fi

    read -r -p "$(echo -e "${YELLOW}$message [y/N]${NC} ")" response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Safe file operation with backup
safe_file_operation() {
    local file="$1"
    local operation="$2"

    if [[ -f "$file" ]]; then
        local backup="${file}.bak.$(date +%Y%m%d_%H%M%S)"
        cp "$file" "$backup"
        log_debug "Backup created: $backup"
    fi

    $operation
}

# Print script header
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$SCRIPT_NAME v$SCRIPT_VERSION${NC}"
    echo -e "${BLUE}$SCRIPT_DESCRIPTION${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Print usage information
usage() {
    cat << EOF
Usage: $SCRIPT_FILE [OPTIONS]

$SCRIPT_DESCRIPTION

Options:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -d, --dry-run       Perform a dry run without making changes
    -n, --no-lock       Disable lock file (allow multiple instances)
    --no-log            Disable file logging
    --version           Show version information

Examples:
    $SCRIPT_FILE                    # Run with defaults
    $SCRIPT_FILE -v                 # Run with verbose output
    $SCRIPT_FILE --dry-run          # Perform dry run
    $SCRIPT_FILE -n                 # Allow multiple instances

EOF
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -n|--no-lock)
                ENABLE_LOCK_FILE=false
                shift
                ;;
            --no-log)
                ENABLE_LOGGING=false
                shift
                ;;
            --version)
                echo "$SCRIPT_NAME v$SCRIPT_VERSION"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# MAIN LOGIC
# =============================================================================

# Initialize script
initialize() {
    log_info "Initializing $SCRIPT_NAME v$SCRIPT_VERSION"

    setup_logging
    acquire_lock

    # Validate environment
    validate_commands || exit 1
    validate_environment || exit 1
    validate_paths || exit 1

    log_debug "Initialization complete"
}

# Main function - implement your logic here
main() {
    log_info "Starting main execution"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "Running in DRY RUN mode - no changes will be made"
    fi

    # =================================
    # YOUR CODE GOES HERE
    # =================================

    # Example: Retry an operation
    # retry some_command --with-args

    # Example: Conditional execution
    # if [[ "$DRY_RUN" != "true" ]]; then
    #     perform_operation
    # else
    #     log_info "DRY RUN: Would perform operation"
    # fi

    # Example: Process files
    # for file in "$SKIPPY_BASE_PATH"/*.txt; do
    #     if [[ -f "$file" ]]; then
    #         log_debug "Processing: $file"
    #         process_file "$file"
    #     fi
    # done

    # Placeholder success message
    log_success "Main execution completed successfully"

    # =================================
    # END OF YOUR CODE
    # =================================
}

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

# Only run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments "$@"

    if [[ "$VERBOSE" == "true" ]]; then
        print_header
    fi

    initialize
    main
fi
