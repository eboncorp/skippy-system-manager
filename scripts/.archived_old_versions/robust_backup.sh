#!/usr/bin/env bash
#
# Skippy System Manager - Robust Backup Script
# Version: 1.0.0
# Created: 2025-11-16
# Based on: robust_template.sh
#
# Performs system backups with comprehensive error handling,
# retry logic, and logging.
#

# =============================================================================
# STRICT MODE
# =============================================================================
set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# SCRIPT METADATA
# =============================================================================
readonly SCRIPT_NAME="robust_backup"
readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DESCRIPTION="Robust system backup with error handling and retry logic"
readonly SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# CONFIGURATION
# =============================================================================
SKIPPY_BASE_PATH="${SKIPPY_BASE_PATH:-/home/dave/skippy}"
BACKUP_BASE_PATH="${BACKUP_BASE_PATH:-$SKIPPY_BASE_PATH/backups}"
LOG_DIR="${SKIPPY_BASE_PATH}/logs"
LOG_FILE="${LOG_DIR}/${SCRIPT_NAME}.log"
LOCK_FILE="/tmp/${SCRIPT_NAME}.lock"

# Backup settings
BACKUP_DIRS=("$SKIPPY_BASE_PATH/scripts" "$SKIPPY_BASE_PATH/configs")
BACKUP_RETENTION_DAYS=30
COMPRESSION_LEVEL=6
MAX_BACKUP_SIZE_MB=1000

# Retry settings
MAX_RETRIES=3
RETRY_DELAY=5
RETRY_BACKOFF_MULTIPLIER=2

# Feature flags
ENABLE_LOCK_FILE=true
ENABLE_LOGGING=true
ENABLE_COMPRESSION=true
DRY_RUN=false
VERBOSE=false

# =============================================================================
# COLOR OUTPUT
# =============================================================================
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m'
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly NC=''
fi

# =============================================================================
# LOGGING
# =============================================================================
setup_logging() {
    mkdir -p "$LOG_DIR" 2>/dev/null || true
    mkdir -p "$BACKUP_BASE_PATH" 2>/dev/null || true
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    if [[ "$ENABLE_LOGGING" == "true" ]]; then
        echo "[$timestamp] [$level] [$SCRIPT_NAME] $message" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

log_info() {
    log "INFO" "$@"
    [[ "$VERBOSE" == "true" ]] && echo -e "${GREEN}[INFO]${NC} $*" >&2
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

# =============================================================================
# ERROR HANDLING
# =============================================================================
cleanup() {
    local exit_code=$?

    # Remove lock file
    if [[ "$ENABLE_LOCK_FILE" == "true" && -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
    fi

    # Clean up partial backup on error
    if [[ $exit_code -ne 0 && -n "${CURRENT_BACKUP:-}" && -f "$CURRENT_BACKUP" ]]; then
        log_warn "Removing partial backup: $CURRENT_BACKUP"
        rm -f "$CURRENT_BACKUP"
    fi

    if [[ $exit_code -ne 0 ]]; then
        log_error "Backup failed with exit code $exit_code"
    fi

    exit $exit_code
}

trap cleanup EXIT

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
            log_error "Backup already running with PID $pid"
            exit 1
        else
            log_warn "Stale lock file found, removing"
            rm -f "$LOCK_FILE"
        fi
    fi

    echo $$ > "$LOCK_FILE"
    log_info "Lock acquired (PID: $$)"
}

# =============================================================================
# RETRY LOGIC
# =============================================================================
retry() {
    local max_attempts="$MAX_RETRIES"
    local delay="$RETRY_DELAY"
    local attempt=1
    local exit_code=0

    while [[ $attempt -le $max_attempts ]]; do
        log_info "Attempt $attempt/$max_attempts: $*"

        set +e
        "$@"
        exit_code=$?
        set -e

        if [[ $exit_code -eq 0 ]]; then
            return 0
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Attempt $attempt failed. Retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * RETRY_BACKOFF_MULTIPLIER))
        fi

        attempt=$((attempt + 1))
    done

    log_error "Failed after $max_attempts attempts: $*"
    return $exit_code
}

# =============================================================================
# VALIDATION
# =============================================================================
validate_environment() {
    local errors=0

    # Check backup directories exist
    for dir in "${BACKUP_DIRS[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_warn "Backup source directory does not exist: $dir"
            ((errors++))
        fi
    done

    # Check disk space
    local available_mb
    available_mb=$(df -m "$BACKUP_BASE_PATH" | awk 'NR==2 {print $4}')

    if [[ "$available_mb" -lt "$MAX_BACKUP_SIZE_MB" ]]; then
        log_error "Insufficient disk space: ${available_mb}MB available, need ${MAX_BACKUP_SIZE_MB}MB"
        return 1
    fi

    log_info "Disk space OK: ${available_mb}MB available"

    if [[ $errors -gt 0 ]]; then
        log_warn "$errors source directory issue(s) found"
    fi

    return 0
}

# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================
create_backup() {
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')

    local backup_name="skippy_backup_${timestamp}"
    CURRENT_BACKUP="$BACKUP_BASE_PATH/${backup_name}.tar"

    if [[ "$ENABLE_COMPRESSION" == "true" ]]; then
        CURRENT_BACKUP="${CURRENT_BACKUP}.gz"
    fi

    log_info "Creating backup: $CURRENT_BACKUP"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would create backup of: ${BACKUP_DIRS[*]}"
        return 0
    fi

    # Create backup with retry logic
    local tar_opts="-cf"
    if [[ "$ENABLE_COMPRESSION" == "true" ]]; then
        tar_opts="-czf"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        tar_opts="${tar_opts}v"
    fi

    local backup_cmd="tar $tar_opts $CURRENT_BACKUP"

    # Add directories that exist
    for dir in "${BACKUP_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            backup_cmd="$backup_cmd $dir"
        fi
    done

    # Execute with retry
    retry bash -c "$backup_cmd" || {
        log_error "Backup creation failed"
        return 1
    }

    # Verify backup
    if [[ -f "$CURRENT_BACKUP" ]]; then
        local size_mb
        size_mb=$(du -m "$CURRENT_BACKUP" | cut -f1)
        log_success "Backup created: $CURRENT_BACKUP (${size_mb}MB)"
    else
        log_error "Backup file not created"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than ${BACKUP_RETENTION_DAYS} days"

    if [[ "$DRY_RUN" == "true" ]]; then
        local old_backups
        old_backups=$(find "$BACKUP_BASE_PATH" -name "skippy_backup_*.tar*" -mtime +$BACKUP_RETENTION_DAYS -type f 2>/dev/null | wc -l)
        log_info "DRY RUN: Would remove $old_backups old backup(s)"
        return 0
    fi

    local count=0
    while IFS= read -r -d '' file; do
        log_info "Removing old backup: $(basename "$file")"
        rm -f "$file"
        ((count++))
    done < <(find "$BACKUP_BASE_PATH" -name "skippy_backup_*.tar*" -mtime +$BACKUP_RETENTION_DAYS -type f -print0 2>/dev/null)

    log_info "Removed $count old backup(s)"
}

verify_backup_integrity() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would verify backup integrity"
        return 0
    fi

    if [[ ! -f "$CURRENT_BACKUP" ]]; then
        log_error "Backup file not found for verification"
        return 1
    fi

    log_info "Verifying backup integrity..."

    local test_opts="-tzf"
    if [[ "$CURRENT_BACKUP" != *.gz ]]; then
        test_opts="-tf"
    fi

    if tar $test_opts "$CURRENT_BACKUP" > /dev/null 2>&1; then
        log_success "Backup integrity verified"
        return 0
    else
        log_error "Backup integrity check failed"
        return 1
    fi
}

generate_backup_report() {
    local report_file="$BACKUP_BASE_PATH/backup_report.txt"

    {
        echo "Skippy Backup Report"
        echo "===================="
        echo "Generated: $(date)"
        echo ""
        echo "Latest Backup: ${CURRENT_BACKUP:-N/A}"
        if [[ -f "${CURRENT_BACKUP:-}" ]]; then
            echo "Size: $(du -h "$CURRENT_BACKUP" | cut -f1)"
        fi
        echo ""
        echo "All Backups:"
        ls -lh "$BACKUP_BASE_PATH"/*.tar* 2>/dev/null | tail -10 || echo "No backups found"
        echo ""
        echo "Disk Usage:"
        df -h "$BACKUP_BASE_PATH"
    } > "$report_file"

    log_info "Backup report saved to $report_file"
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

$SCRIPT_DESCRIPTION

Options:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -d, --dry-run       Perform a dry run without making changes
    -n, --no-lock       Allow multiple instances
    --no-compress       Disable compression
    --retention DAYS    Set backup retention (default: $BACKUP_RETENTION_DAYS)
    --version           Show version information

Examples:
    $(basename "$0")                    # Run backup
    $(basename "$0") -v                 # Verbose output
    $(basename "$0") --dry-run          # Dry run
    $(basename "$0") --retention 60     # Keep backups for 60 days

EOF
}

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
            --no-compress)
                ENABLE_COMPRESSION=false
                shift
                ;;
            --retention)
                BACKUP_RETENTION_DAYS="$2"
                shift 2
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
# MAIN
# =============================================================================
main() {
    log_info "Starting $SCRIPT_NAME v$SCRIPT_VERSION"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "Running in DRY RUN mode - no changes will be made"
    fi

    # Setup
    setup_logging
    acquire_lock

    # Validation
    validate_environment || exit 1

    # Backup operations
    create_backup || exit 1
    verify_backup_integrity || exit 1
    cleanup_old_backups
    generate_backup_report

    log_success "Backup completed successfully"
}

# Only run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments "$@"
    main
fi
