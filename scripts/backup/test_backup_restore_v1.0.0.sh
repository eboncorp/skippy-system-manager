#!/bin/bash
# Backup Test and Restore Script
# Tests backup integrity and restore functionality

BACKUP_ROOT="googledrive:Backups/ebonhawk-full"
TEST_DIR="/tmp/backup_restore_test_$(date +%s)"
LOG_FILE="/home/dave/.backup_logs/restore_test_$(date +%Y%m%d).log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cleanup_test() {
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
        log_message "Cleaned up test directory: $TEST_DIR"
    fi
}

# Trap to ensure cleanup on exit
trap cleanup_test EXIT

test_backup_integrity() {
    local BACKUP_DATE="$1"

    if [ -z "$BACKUP_DATE" ]; then
        BACKUP_DATE=$(date +%Y-%m-%d)
    fi

    log_message "========================================="
    log_message "Starting backup integrity test"
    log_message "Testing backup: $BACKUP_DATE"
    log_message "========================================="

    # Create test directory
    mkdir -p "$TEST_DIR"

    # Test 1: Verify backup exists
    log_message "Test 1: Checking if backup exists..."
    if rclone lsd "$BACKUP_ROOT/$BACKUP_DATE" >/dev/null 2>&1; then
        log_message "  ✓ Backup directory exists"
    else
        log_message "  ✗ Backup directory not found!"
        return 1
    fi

    # Test 2: Check backup size and file count
    log_message "Test 2: Checking backup statistics..."
    BACKUP_INFO=$(rclone size "$BACKUP_ROOT/$BACKUP_DATE" --json 2>/dev/null)
    if [ $? -eq 0 ]; then
        FILES=$(echo "$BACKUP_INFO" | jq -r '.count // 0')
        BYTES=$(echo "$BACKUP_INFO" | jq -r '.bytes // 0')
        SIZE_HUMAN=$(numfmt --to=iec $BYTES)

        log_message "  ✓ Backup contains $FILES files ($SIZE_HUMAN)"

        if [ "$FILES" -lt 100 ]; then
            log_message "  ⚠ Warning: Low file count ($FILES files)"
        fi

        if [ "$BYTES" -lt 1048576 ]; then  # Less than 1MB
            log_message "  ⚠ Warning: Small backup size ($SIZE_HUMAN)"
        fi
    else
        log_message "  ✗ Failed to get backup statistics"
        return 1
    fi

    # Test 3: Test critical directories
    log_message "Test 3: Checking critical directories..."
    CRITICAL_DIRS=("Documents" "Scripts" "Config" ".ssh" "Skippy")

    for DIR in "${CRITICAL_DIRS[@]}"; do
        if rclone lsd "$BACKUP_ROOT/$BACKUP_DATE/$DIR" >/dev/null 2>&1; then
            log_message "  ✓ $DIR directory found"
        else
            log_message "  ⚠ $DIR directory missing or empty"
        fi
    done

    # Test 4: Sample file restore test
    log_message "Test 4: Testing file restore functionality..."

    # Find a small file to test with
    TEST_FILE=$(rclone lsf "$BACKUP_ROOT/$BACKUP_DATE/Scripts/" --max-depth 1 --files-only 2>/dev/null | head -1)

    if [ -n "$TEST_FILE" ]; then
        log_message "  Testing restore of: Scripts/$TEST_FILE"

        # Restore the file
        if rclone copy "$BACKUP_ROOT/$BACKUP_DATE/Scripts/$TEST_FILE" "$TEST_DIR/" 2>/dev/null; then
            if [ -f "$TEST_DIR/$TEST_FILE" ]; then
                RESTORED_SIZE=$(stat -c%s "$TEST_DIR/$TEST_FILE" 2>/dev/null || echo "0")
                log_message "  ✓ File restored successfully ($RESTORED_SIZE bytes)"

                # Compare with original if it exists
                if [ -f "/home/dave/Scripts/$TEST_FILE" ]; then
                    ORIGINAL_SIZE=$(stat -c%s "/home/dave/Scripts/$TEST_FILE")
                    if [ "$RESTORED_SIZE" -eq "$ORIGINAL_SIZE" ]; then
                        log_message "  ✓ File size matches original"
                    else
                        log_message "  ⚠ File size mismatch: restored($RESTORED_SIZE) vs original($ORIGINAL_SIZE)"
                    fi
                fi
            else
                log_message "  ✗ File restore failed - file not found after copy"
                return 1
            fi
        else
            log_message "  ✗ File restore failed - rclone copy failed"
            return 1
        fi
    else
        log_message "  ⚠ No test file found in Scripts directory"
    fi

    # Test 5: Check recent backup timestamps
    log_message "Test 5: Checking backup recency..."
    BACKUP_TIMESTAMP=$(rclone lsl "$BACKUP_ROOT" --dirs-only | grep "$BACKUP_DATE" | head -1)
    if [ -n "$BACKUP_TIMESTAMP" ]; then
        log_message "  ✓ Backup timestamp verified"
    else
        log_message "  ⚠ Could not verify backup timestamp"
    fi

    log_message ""
    log_message "========================================="
    log_message "Backup integrity test completed"
    log_message "========================================="

    return 0
}

restore_directory() {
    local SOURCE_DIR="$1"
    local DEST_DIR="$2"
    local BACKUP_DATE="$3"

    if [ -z "$BACKUP_DATE" ]; then
        BACKUP_DATE=$(date +%Y-%m-%d)
    fi

    log_message "Restoring $SOURCE_DIR to $DEST_DIR from backup $BACKUP_DATE..."

    # Create destination directory
    mkdir -p "$DEST_DIR"

    # Perform restore
    if rclone copy "$BACKUP_ROOT/$BACKUP_DATE/$SOURCE_DIR" "$DEST_DIR" --progress 2>&1 | tee -a "$LOG_FILE"; then
        log_message "✓ Restore completed successfully"

        # Show summary
        RESTORED_COUNT=$(find "$DEST_DIR" -type f | wc -l)
        RESTORED_SIZE=$(du -sh "$DEST_DIR" 2>/dev/null | cut -f1)
        log_message "Restored: $RESTORED_COUNT files ($RESTORED_SIZE)"

        return 0
    else
        log_message "✗ Restore failed!"
        return 1
    fi
}

show_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  test [date]           - Test backup integrity (default: today)"
    echo "  restore <src> <dest>  - Restore directory from backup"
    echo "  list                  - List available backups"
    echo "  status               - Show backup status"
    echo ""
    echo "Examples:"
    echo "  $0 test                              # Test today's backup"
    echo "  $0 test 2025-09-21                  # Test specific date"
    echo "  $0 restore Documents /tmp/restore   # Restore Documents folder"
    echo "  $0 list                             # Show all backups"
}

case "${1:-test}" in
    "test")
        test_backup_integrity "$2"
        ;;
    "restore")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Error: restore requires source and destination"
            show_usage
            exit 1
        fi
        restore_directory "$2" "$3" "$4"
        ;;
    "list")
        echo "Available backups:"
        rclone lsd "$BACKUP_ROOT" 2>/dev/null | awk '{print "  " $NF}' | sort -r
        ;;
    "status")
        /home/dave/Scripts/check_backup_status.sh
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac