#!/bin/bash
# Comprehensive Home Directory Backup to Google Drive
# Created: 2025-09-22
# Purpose: Full backup with incremental sync and automatic cleanup

# Configuration
GDRIVE_REMOTE="googledrive:"
BACKUP_ROOT="${GDRIVE_REMOTE}Backups/ebonhawk-full"
LOG_DIR="/home/dave/.backup_logs"
LOG_FILE="${LOG_DIR}/gdrive_backup_$(date +%Y%m%d).log"
HOME_DIR="/home/dave"
MAX_PARALLEL=4  # Number of parallel transfers
RETENTION_DAYS=30  # Keep backups for 30 days

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check available space
check_space() {
    log_message "Checking Google Drive space..."
    QUOTA_INFO=$(rclone about "$GDRIVE_REMOTE" --json 2>/dev/null)
    if [ $? -eq 0 ]; then
        TOTAL=$(echo "$QUOTA_INFO" | jq -r '.total // 0')
        USED=$(echo "$QUOTA_INFO" | jq -r '.used // 0')
        FREE=$(echo "$QUOTA_INFO" | jq -r '.free // 0')

        if [ "$TOTAL" != "0" ]; then
            PERCENT=$((USED * 100 / TOTAL))
            log_message "Google Drive: $(numfmt --to=iec $USED) used / $(numfmt --to=iec $TOTAL) total (${PERCENT}% used)"

            if [ "$PERCENT" -gt 90 ]; then
                log_message "WARNING: Google Drive is ${PERCENT}% full!"
            fi
        fi
    fi
}

# Function to backup a directory with progress
backup_directory() {
    local SOURCE="$1"
    local DEST="$2"
    local DESC="$3"

    if [ ! -d "$SOURCE" ]; then
        log_message "Skipping $DESC - directory not found: $SOURCE"
        return 1
    fi

    log_message "Backing up $DESC..."

    # Calculate size for progress reporting
    SIZE=$(du -sh "$SOURCE" 2>/dev/null | cut -f1)
    log_message "  Size: $SIZE"

    # Perform the backup with optimizations
    rclone sync "$SOURCE" "$DEST" \
        --transfers=$MAX_PARALLEL \
        --checkers=8 \
        --fast-list \
        --progress \
        --stats-one-line \
        --stats 10s \
        --exclude-from=/home/dave/Scripts/backup_excludes.txt \
        --log-file="$LOG_FILE" \
        --log-level=INFO \
        2>&1 | while read line; do
            if [[ "$line" == *"Transferred:"* ]]; then
                echo -ne "\r  $line"
            fi
        done

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_message "  ✓ $DESC backup completed"
        return 0
    else
        log_message "  ✗ $DESC backup failed!"
        return 1
    fi
}

# Main backup process
main() {
    log_message "========================================="
    log_message "Starting comprehensive home backup"
    log_message "========================================="

    # Check if rclone is configured
    if ! rclone listremotes | grep -q "^googledrive:"; then
        log_message "ERROR: Google Drive remote not configured in rclone"
        exit 1
    fi

    # Check available space
    check_space

    # Create backup timestamp
    BACKUP_DATE=$(date +%Y-%m-%d)
    BACKUP_PATH="${BACKUP_ROOT}/${BACKUP_DATE}"

    log_message "Backup destination: $BACKUP_PATH"

    # Critical directories (backup first)
    CRITICAL_DIRS=(
        "Documents:Important documents"
        "Scripts:System scripts"
        "Config:Configuration files"
        ".ssh:SSH keys and config"
        "Skippy:Infrastructure project"
        ".nexus:Nexus configuration"
    )

    # Standard directories
    STANDARD_DIRS=(
        "Desktop:Desktop files"
        "Downloads:Downloaded files"
        "Pictures:Images and photos"
        "Utilities:Utility programs"
        "Scans:Scanned documents"
        ".local/share:Application data"
        ".config:User configurations"
    )

    # Large/optional directories (backup last)
    LARGE_DIRS=(
        "Videos:Video files"
        "Music:Music files"
        ".cache:Cache files"
    )

    FAILED_DIRS=()
    SUCCESS_COUNT=0
    TOTAL_COUNT=0

    # Backup critical directories
    log_message ""
    log_message "Phase 1: Critical Directories"
    log_message "-----------------------------"
    for DIR_INFO in "${CRITICAL_DIRS[@]}"; do
        IFS=':' read -r DIR DESC <<< "$DIR_INFO"
        ((TOTAL_COUNT++))
        if backup_directory "${HOME_DIR}/${DIR}" "${BACKUP_PATH}/${DIR}" "$DESC"; then
            ((SUCCESS_COUNT++))
        else
            FAILED_DIRS+=("$DIR")
        fi
    done

    # Backup standard directories
    log_message ""
    log_message "Phase 2: Standard Directories"
    log_message "-----------------------------"
    for DIR_INFO in "${STANDARD_DIRS[@]}"; do
        IFS=':' read -r DIR DESC <<< "$DIR_INFO"
        ((TOTAL_COUNT++))
        if backup_directory "${HOME_DIR}/${DIR}" "${BACKUP_PATH}/${DIR}" "$DESC"; then
            ((SUCCESS_COUNT++))
        else
            FAILED_DIRS+=("$DIR")
        fi
    done

    # Backup large directories (if space permits)
    log_message ""
    log_message "Phase 3: Large/Optional Directories"
    log_message "------------------------------------"
    for DIR_INFO in "${LARGE_DIRS[@]}"; do
        IFS=':' read -r DIR DESC <<< "$DIR_INFO"
        # Check space before backing up large dirs
        check_space
        ((TOTAL_COUNT++))
        if backup_directory "${HOME_DIR}/${DIR}" "${BACKUP_PATH}/${DIR}" "$DESC"; then
            ((SUCCESS_COUNT++))
        else
            FAILED_DIRS+=("$DIR")
        fi
    done

    # Clean up old backups
    log_message ""
    log_message "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)

    rclone lsf "$BACKUP_ROOT" --dirs-only 2>/dev/null | while read BACKUP_DIR; do
        BACKUP_DIR=${BACKUP_DIR%/}  # Remove trailing slash
        if [[ "$BACKUP_DIR" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && [[ "$BACKUP_DIR" < "$CUTOFF_DATE" ]]; then
            log_message "  Removing old backup: $BACKUP_DIR"
            rclone purge "${BACKUP_ROOT}/${BACKUP_DIR}" 2>&1 | tee -a "$LOG_FILE"
        fi
    done

    # Clean up old log files (older than $RETENTION_DAYS days)
    log_message ""
    log_message "Cleaning up old log files (older than $RETENTION_DAYS days)..."
    LOGS_REMOVED=0
    find "$LOG_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS -print0 | while IFS= read -r -d '' OLD_LOG; do
        log_message "  Removing old log: $(basename $OLD_LOG)"
        rm -f "$OLD_LOG"
        ((LOGS_REMOVED++))
    done
    if [ $LOGS_REMOVED -gt 0 ]; then
        log_message "  Removed $LOGS_REMOVED old log files"
    else
        log_message "  No old logs to remove"
    fi

    # Final summary
    log_message ""
    log_message "========================================="
    log_message "Backup Summary"
    log_message "========================================="
    log_message "Successful: $SUCCESS_COUNT / $TOTAL_COUNT directories"

    if [ ${#FAILED_DIRS[@]} -gt 0 ]; then
        log_message "Failed directories:"
        for DIR in "${FAILED_DIRS[@]}"; do
            log_message "  - $DIR"
        done
    fi

    # Check final space usage
    check_space

    log_message "Backup completed at $(date)"
    log_message "Log saved to: $LOG_FILE"

    # Send notification if available
    if command -v notify-send &> /dev/null; then
        if [ ${#FAILED_DIRS[@]} -eq 0 ]; then
            notify-send "Backup Complete" "Successfully backed up $SUCCESS_COUNT directories to Google Drive" -i checkbox-checked
        else
            notify-send "Backup Complete with Errors" "Backed up $SUCCESS_COUNT/$TOTAL_COUNT directories. Check log for details." -i dialog-warning
        fi
    fi

    # Exit with appropriate code
    if [ ${#FAILED_DIRS[@]} -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"