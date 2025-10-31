#!/bin/bash
# Google Photos Backup Script
# Downloads Google Photos to local storage and backs up to Google Drive

# Configuration
PHOTOS_REMOTE="googlephotos:"
GDRIVE_REMOTE="googledrive:"
LOCAL_BACKUP_DIR="/home/dave/GooglePhotosBackup"
GDRIVE_BACKUP_PATH="${GDRIVE_REMOTE}Backups/GooglePhotos"
LOG_DIR="/home/dave/.backup_logs"
LOG_FILE="${LOG_DIR}/google_photos_backup_$(date +%Y%m%d).log"

# Create directories
mkdir -p "$LOCAL_BACKUP_DIR" "$LOG_DIR"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "==========================================="
log_message "Starting Google Photos backup"
log_message "==========================================="

# Function to backup photos by year
backup_photos_by_year() {
    local year=$1
    local local_year_dir="${LOCAL_BACKUP_DIR}/${year}"
    local gdrive_year_path="${GDRIVE_BACKUP_PATH}/${year}"

    log_message "Processing photos from year: $year"
    mkdir -p "$local_year_dir"

    # Download photos for this year
    log_message "Downloading $year photos to local storage..."
    if rclone copy "${PHOTOS_REMOTE}media/by-year/$year" "$local_year_dir" \
        --progress --transfers 4 --checkers 8 \
        --log-file="$LOG_FILE" --log-level INFO; then
        log_message "✓ Downloaded $year photos successfully"

        # Backup to Google Drive
        log_message "Backing up $year photos to Google Drive..."
        if rclone sync "$local_year_dir" "$gdrive_year_path" \
            --progress --transfers 4 --checkers 8 \
            --log-file="$LOG_FILE" --log-level INFO; then
            log_message "✓ Backed up $year photos to Google Drive"
        else
            log_message "✗ Failed to backup $year photos to Google Drive"
        fi
    else
        log_message "✗ Failed to download $year photos"
    fi
}

# Function to backup all albums
backup_albums() {
    local albums_dir="${LOCAL_BACKUP_DIR}/Albums"
    local gdrive_albums_path="${GDRIVE_BACKUP_PATH}/Albums"

    log_message "Processing photo albums..."
    mkdir -p "$albums_dir"

    # List and backup each album
    rclone lsd "${PHOTOS_REMOTE}album/" 2>/dev/null | while read -r line; do
        if [[ $line =~ -1[[:space:]]+[0-9-]+[[:space:]]+[0-9:]+[[:space:]]+[0-9]+[[:space:]]+(.+)$ ]]; then
            album_name="${BASH_REMATCH[1]}"
            album_dir="${albums_dir}/${album_name}"

            log_message "Processing album: $album_name"
            mkdir -p "$album_dir"

            # Download album
            if rclone copy "${PHOTOS_REMOTE}album/${album_name}" "$album_dir" \
                --progress --transfers 2 --checkers 4 \
                --log-file="$LOG_FILE" --log-level INFO; then
                log_message "✓ Downloaded album: $album_name"

                # Backup to Google Drive
                rclone sync "$album_dir" "${gdrive_albums_path}/${album_name}" \
                    --progress --transfers 2 --checkers 4 \
                    --log-file="$LOG_FILE" --log-level INFO
                log_message "✓ Backed up album: $album_name"
            else
                log_message "✗ Failed to download album: $album_name"
            fi
        fi
    done
}

# Function to backup recent photos
backup_recent_photos() {
    local recent_dir="${LOCAL_BACKUP_DIR}/Recent"
    local gdrive_recent_path="${GDRIVE_BACKUP_PATH}/Recent"

    log_message "Processing recent photos..."
    mkdir -p "$recent_dir"

    # Download recent photos (last 30 days)
    log_message "Downloading recent photos..."
    if rclone copy "${PHOTOS_REMOTE}media" "$recent_dir" \
        --max-age 30d --progress --transfers 4 --checkers 8 \
        --log-file="$LOG_FILE" --log-level INFO; then
        log_message "✓ Downloaded recent photos"

        # Backup to Google Drive
        rclone sync "$recent_dir" "$gdrive_recent_path" \
            --progress --transfers 4 --checkers 8 \
            --log-file="$LOG_FILE" --log-level INFO
        log_message "✓ Backed up recent photos to Google Drive"
    else
        log_message "✗ Failed to download recent photos"
    fi
}

# Check Google Photos access
log_message "Testing Google Photos access..."
if ! rclone lsd "$PHOTOS_REMOTE" >/dev/null 2>&1; then
    log_message "✗ Cannot access Google Photos. Check authentication."
    exit 1
fi
log_message "✓ Google Photos access confirmed"

# Check Google Drive access
log_message "Testing Google Drive access..."
if ! rclone lsd "$GDRIVE_REMOTE" >/dev/null 2>&1; then
    log_message "✗ Cannot access Google Drive. Check authentication."
    exit 1
fi
log_message "✓ Google Drive access confirmed"

# Main backup process
case "${1:-all}" in
    "recent")
        backup_recent_photos
        ;;
    "albums")
        backup_albums
        ;;
    "year")
        if [[ -n "$2" ]]; then
            backup_photos_by_year "$2"
        else
            log_message "Usage: $0 year YYYY"
            exit 1
        fi
        ;;
    "all")
        backup_recent_photos
        backup_albums
        ;;
    *)
        echo "Usage: $0 [recent|albums|year YYYY|all]"
        echo "  recent  - Backup photos from last 30 days"
        echo "  albums  - Backup all photo albums"
        echo "  year    - Backup specific year (requires year as second argument)"
        echo "  all     - Backup recent photos and albums (default)"
        exit 1
        ;;
esac

# Final summary
log_message "==========================================="
log_message "Google Photos backup completed"
log_message "Local backup location: $LOCAL_BACKUP_DIR"
log_message "Google Drive backup: $GDRIVE_BACKUP_PATH"
log_message "==========================================="

# Send notification
if command -v /home/dave/Scripts/backup_email_notifier.sh >/dev/null 2>&1; then
    /home/dave/Scripts/backup_email_notifier.sh "Google Photos Backup Complete" \
        "Google Photos backup finished successfully. Check $LOG_FILE for details."
fi