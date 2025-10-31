#!/bin/bash

# TidyTux Enhanced - Comprehensive Linux System Cleanup Utility
# Version 2.1.0
# Created: March 2025
# 
# Key Improvements in v2.1:
#  - Enhanced error handling and input validation
#  - Improved security with safer file operations
#  - Better dependency management and auto-installation
#  - Structured logging with JSON output option
#  - More robust configuration management
#  - Enhanced progress tracking and resource monitoring
#  - Better signal handling and cleanup
#  - Modular architecture for better maintainability
#  - Cross-platform compatibility improvements
#  - Enhanced backup functionality
#  - Memory-efficient large file operations
#  - Improved parallel processing with job control

VERSION="2.1.0"
PROGRAM_NAME="TidyTux Enhanced"
PROGRAM_DESCRIPTION="Advanced Linux System Cleanup and Optimization Utility"
GITHUB_REPO="https://github.com/username/tidytux"

# Strict error handling
set -euo pipefail
IFS=$'\n\t'

# Security: Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "ERROR: This script should NOT be run as root for security reasons" >&2
    exit 1
fi

# Validate environment
if [ -z "${HOME:-}" ] || [ ! -d "${HOME}" ]; then
    echo "ERROR: Invalid HOME directory environment" >&2
    exit 1
fi

# Global constants and variables
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_DIR="${HOME}/.config/tidytux"
readonly CACHE_DIR="${HOME}/.cache/tidytux"
readonly BACKUP_DIR="${HOME}/.local/share/tidytux/backups"
readonly LOG_DIR="${HOME}/.local/share/tidytux/logs"
readonly CONFIG_FILE="${CONFIG_DIR}/config.ini"
readonly SESSION_ID="$(date +%Y%m%d_%H%M%S)_$$"
readonly LOG_FILE="${LOG_DIR}/tidytux_${SESSION_ID}.log"
readonly JSON_LOG_FILE="${LOG_DIR}/tidytux_${SESSION_ID}.json"
readonly LOCK_FILE="/tmp/tidytux.lock"

# Create required directories
for dir in "$CONFIG_DIR" "$CACHE_DIR" "$BACKUP_DIR" "$LOG_DIR"; do
    mkdir -p "$dir" || {
        echo "ERROR: Cannot create directory: $dir" >&2
        exit 1
    }
done

# Color definitions (with fallback for non-interactive shells)
if [ -t 1 ]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly PURPLE='\033[0;35m'
    readonly CYAN='\033[0;36m'
    readonly BOLD='\033[1m'
    readonly NC='\033[0m'
else
    readonly RED='' GREEN='' YELLOW='' BLUE='' PURPLE='' CYAN='' BOLD='' NC=''
fi

# Configuration defaults
INTERACTIVE=true
SKIP_CONFIRMATION=false
VERBOSE=false
DRY_RUN=false
EMERGENCY_MODE=false
PARALLEL_JOBS=4
ENABLE_MONITORING=true
JSON_OUTPUT=false
COMPRESSION_LEVEL=6
MAX_LOG_SIZE="100M"
MAX_BACKUP_AGE=30

# Performance tracking
START_TIME=$(date +%s)
CLEANED_FILES=0
SPACE_SAVED=0
ERRORS_COUNT=0
WARNINGS_COUNT=0

# Signal handling
trap 'cleanup_and_exit 130' INT TERM
trap 'cleanup_temp_files' EXIT

# === UTILITY FUNCTIONS ===

# Logging functions with structured output
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Console output
    case "$level" in
        "INFO")  [ "$INTERACTIVE" = true ] && echo -e "${GREEN}[$timestamp]${NC} $message" ;;
        "WARN")  [ "$INTERACTIVE" = true ] && echo -e "${YELLOW}[$timestamp] WARNING:${NC} $message"; ((WARNINGS_COUNT++)) ;;
        "ERROR") [ "$INTERACTIVE" = true ] && echo -e "${RED}[$timestamp] ERROR:${NC} $message" >&2; ((ERRORS_COUNT++)) ;;
        "DEBUG") [ "$VERBOSE" = true ] && echo -e "${CYAN}[$timestamp] DEBUG:${NC} $message" ;;
    esac
    
    # File logging
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # JSON logging
    if [ "$JSON_OUTPUT" = true ]; then
        printf '{"timestamp":"%s","level":"%s","message":"%s","session_id":"%s"}\n' \
               "$timestamp" "$level" "$message" "$SESSION_ID" >> "$JSON_LOG_FILE"
    fi
}

log_info() { log "INFO" "$1"; }
log_warn() { log "WARN" "$1"; }
log_error() { log "ERROR" "$1"; }
log_debug() { log "DEBUG" "$1"; }

# Lock management
acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_error "Another instance of TidyTux is already running (PID: $pid)"
            exit 1
        else
            log_warn "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
    log_debug "Acquired lock file: $LOCK_FILE"
}

release_lock() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
        log_debug "Released lock file"
    fi
}

# Cleanup functions
cleanup_temp_files() {
    local temp_files=(/tmp/tidytux_* /tmp/.tidytux_*)
    for file in "${temp_files[@]}"; do
        [ -f "$file" ] && rm -f "$file" 2>/dev/null
    done
}

cleanup_and_exit() {
    local exit_code=${1:-0}
    log_info "Cleaning up and exiting..."
    cleanup_temp_files
    release_lock
    
    # Generate final report
    generate_final_report
    
    exit "$exit_code"
}

# Configuration management
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log_debug "Loading configuration from $CONFIG_FILE"
        # Safely source configuration
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue
            
            # Validate and set configuration
            case "$key" in
                PARALLEL_JOBS) PARALLEL_JOBS="$value" ;;
                COMPRESSION_LEVEL) COMPRESSION_LEVEL="$value" ;;
                MAX_BACKUP_AGE) MAX_BACKUP_AGE="$value" ;;
                ENABLE_MONITORING) ENABLE_MONITORING="$value" ;;
                JSON_OUTPUT) JSON_OUTPUT="$value" ;;
            esac
        done < "$CONFIG_FILE"
    else
        create_default_config
    fi
}

create_default_config() {
    log_info "Creating default configuration file"
    cat > "$CONFIG_FILE" << 'EOF'
# TidyTux Enhanced Configuration File
# Version 2.1.0

# Performance settings
PARALLEL_JOBS=4
COMPRESSION_LEVEL=6

# Backup settings
MAX_BACKUP_AGE=30

# Monitoring and logging
ENABLE_MONITORING=true
JSON_OUTPUT=false

# Cleanup behavior
AGGRESSIVE_CLEANUP=false
PRESERVE_LOGS=true

# File type handling
ORGANIZE_DOWNLOADS=true
CLEAN_BROWSER_CACHE=true
CLEAN_SYSTEM_CACHE=true
CLEAN_DOCKER=true
CLEAN_SNAPS=true
EOF
}

# System resource monitoring
check_system_resources() {
    local available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7*100/$2}')
    local disk_usage=$(df "$HOME" | awk 'NR==2{print $(NF-1)}' | sed 's/%//')
    
    log_debug "Available memory: ${available_memory}%"
    log_debug "Disk usage: ${disk_usage}%"
    
    if (( $(echo "$available_memory < 10" | bc -l) )); then
        log_warn "Low memory available (${available_memory}%)"
        PARALLEL_JOBS=$((PARALLEL_JOBS / 2))
        [ "$PARALLEL_JOBS" -lt 1 ] && PARALLEL_JOBS=1
    fi
    
    if [ "$disk_usage" -gt 95 ]; then
        log_warn "Critical disk space (${disk_usage}% used) - enabling emergency mode"
        EMERGENCY_MODE=true
    elif [ "$disk_usage" -gt 85 ]; then
        log_warn "High disk usage (${disk_usage}% used)"
    fi
}

# Dependency checking and installation
check_dependencies() {
    local required_tools=("find" "du" "df" "xargs" "parallel")
    local optional_tools=("fdupes" "bleachbit" "docker" "snap" "flatpak")
    local missing_required=()
    local missing_optional=()