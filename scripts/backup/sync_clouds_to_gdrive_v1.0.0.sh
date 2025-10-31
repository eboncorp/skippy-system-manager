#!/bin/bash
# Sync OneDrive and Dropbox content to Google Drive
# Ensures all cloud storage is backed up to a single location

LOG_FILE="/home/dave/.backup_logs/cloud_sync_$(date +%Y%m%d).log"
GDRIVE_CLOUD_BACKUP="googledrive:CloudBackups"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

sync_cloud_service() {
    local SOURCE="$1"
    local DEST="$2"
    local NAME="$3"

    log_message "Syncing $NAME to Google Drive..."

    # Check size first
    SIZE_INFO=$(rclone size "$SOURCE" --json 2>/dev/null)
    if [ $? -eq 0 ]; then
        FILES=$(echo "$SIZE_INFO" | jq -r '.count // 0')
        BYTES=$(echo "$SIZE_INFO" | jq -r '.bytes // 0')
        log_message "  $NAME contains $FILES files ($(numfmt --to=iec $BYTES))"
    fi

    # Perform sync
    rclone sync "$SOURCE" "$DEST" \
        --transfers=4 \
        --checkers=8 \
        --fast-list \
        --progress \
        --stats-one-line \
        --stats 10s \
        --log-file="$LOG_FILE" \
        --log-level=INFO \
        2>&1 | while read line; do
            if [[ "$line" == *"Transferred:"* ]]; then
                echo -ne "\r  $line"
            fi
        done

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_message "  ✓ $NAME sync completed successfully"
        return 0
    else
        log_message "  ✗ $NAME sync failed!"
        return 1
    fi
}

main() {
    log_message "========================================="
    log_message "Starting cloud services sync to Google Drive"
    log_message "========================================="

    # Create backup directory structure
    log_message "Creating backup structure in Google Drive..."
    rclone mkdir "$GDRIVE_CLOUD_BACKUP/OneDrive" 2>/dev/null
    rclone mkdir "$GDRIVE_CLOUD_BACKUP/Dropbox" 2>/dev/null

    # Sync OneDrive
    if rclone listremotes | grep -q "^onedrive:"; then
        sync_cloud_service "onedrive:" "$GDRIVE_CLOUD_BACKUP/OneDrive" "OneDrive"
    else
        log_message "OneDrive not configured in rclone"
    fi

    echo ""

    # Sync Dropbox
    if rclone listremotes | grep -q "^dropbox:"; then
        sync_cloud_service "dropbox:" "$GDRIVE_CLOUD_BACKUP/Dropbox" "Dropbox"
    else
        log_message "Dropbox not configured in rclone"
    fi

    log_message ""
    log_message "========================================="
    log_message "Cloud sync completed at $(date)"
    log_message "========================================="

    # Check final sizes
    log_message ""
    log_message "Final backup sizes in Google Drive:"

    for SERVICE in OneDrive Dropbox; do
        SIZE_INFO=$(rclone size "$GDRIVE_CLOUD_BACKUP/$SERVICE" --json 2>/dev/null)
        if [ $? -eq 0 ]; then
            FILES=$(echo "$SIZE_INFO" | jq -r '.count // 0')
            BYTES=$(echo "$SIZE_INFO" | jq -r '.bytes // 0')
            log_message "  $SERVICE: $FILES files ($(numfmt --to=iec $BYTES))"
        fi
    done
}

# Run main function
main "$@"