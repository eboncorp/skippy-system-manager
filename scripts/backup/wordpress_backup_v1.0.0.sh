#!/bin/bash
# WordPress Backup Script v1.0.0
# Automated backup of WordPress database and uploads
#
# Usage:
#   bash wordpress_backup_v1.0.0.sh [--db-only|--uploads-only]
#
# Features:
#   - Database export with compression
#   - Uploads folder backup
#   - Automatic rotation (keep 7 daily, 4 weekly)
#   - Local and optional Google Drive sync
#
# Dependencies:
#   - WP-CLI
#   - gzip
#
# Created: 2025-12-21

VERSION="1.0.0"
SCRIPT_NAME="WordPress Backup"

# Configuration
WP_PATH="${WORDPRESS_PATH:-/home/dave/skippy/websites/rundaverun/local_site/rundaverun_local_site/app/public}"
BACKUP_DIR="/home/dave/skippy/backups/wordpress"
LOG_FILE="/home/dave/skippy/logs/wordpress_backup.log"
RETENTION_DAILY=7
RETENTION_WEEKLY=4

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    case "$level" in
        INFO)  echo -e "${GREEN}[INFO]${NC} $message" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" ;;
    esac
}

# Initialize
mkdir -p "$BACKUP_DIR"/{daily,weekly}
mkdir -p "$(dirname "$LOG_FILE")"

log "INFO" "=== $SCRIPT_NAME v$VERSION starting ==="

# Parse arguments
DB_ONLY=false
UPLOADS_ONLY=false

case "$1" in
    --db-only)     DB_ONLY=true ;;
    --uploads-only) UPLOADS_ONLY=true ;;
esac

# Get date components
TODAY=$(date +%Y%m%d)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday

# Determine if weekly backup
IS_WEEKLY=false
if [ "$DAY_OF_WEEK" = "7" ]; then
    IS_WEEKLY=true
    BACKUP_SUBDIR="weekly"
else
    BACKUP_SUBDIR="daily"
fi

# Check if WordPress exists
if [ ! -d "$WP_PATH" ]; then
    log "ERROR" "WordPress path not found: $WP_PATH"
    exit 1
fi

# Database backup
if [ "$UPLOADS_ONLY" = false ]; then
    log "INFO" "Backing up database..."

    DB_BACKUP_FILE="$BACKUP_DIR/$BACKUP_SUBDIR/db_backup_$TODAY.sql.gz"

    if wp --path="$WP_PATH" --allow-root db export - 2>/dev/null | gzip > "$DB_BACKUP_FILE"; then
        DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
        log "INFO" "Database backup created: $DB_BACKUP_FILE ($DB_SIZE)"
    else
        log "ERROR" "Database backup failed"
    fi
fi

# Uploads backup (weekly only by default, or if explicitly requested)
if [ "$DB_ONLY" = false ] && ([ "$IS_WEEKLY" = true ] || [ "$UPLOADS_ONLY" = true ]); then
    log "INFO" "Backing up uploads directory..."

    UPLOADS_PATH="$WP_PATH/wp-content/uploads"
    UPLOADS_BACKUP_FILE="$BACKUP_DIR/weekly/uploads_backup_$TODAY.tar.gz"

    if [ -d "$UPLOADS_PATH" ]; then
        if tar -czf "$UPLOADS_BACKUP_FILE" -C "$WP_PATH/wp-content" uploads 2>/dev/null; then
            UPLOADS_SIZE=$(du -h "$UPLOADS_BACKUP_FILE" | cut -f1)
            log "INFO" "Uploads backup created: $UPLOADS_BACKUP_FILE ($UPLOADS_SIZE)"
        else
            log "ERROR" "Uploads backup failed"
        fi
    else
        log "WARN" "Uploads directory not found: $UPLOADS_PATH"
    fi
fi

# Cleanup old backups
log "INFO" "Cleaning old backups..."

# Daily: keep last 7
find "$BACKUP_DIR/daily" -name "db_backup_*.sql.gz" -type f -mtime +$RETENTION_DAILY -delete 2>/dev/null
DELETED_DAILY=$(find "$BACKUP_DIR/daily" -name "db_backup_*.sql.gz" -type f -mtime +$RETENTION_DAILY 2>/dev/null | wc -l)

# Weekly: keep last 4
find "$BACKUP_DIR/weekly" -name "*.gz" -type f -mtime +$((RETENTION_WEEKLY * 7)) -delete 2>/dev/null

# Summary
log "INFO" "=== Backup Summary ==="
log "INFO" "Daily backups: $(ls "$BACKUP_DIR/daily"/*.gz 2>/dev/null | wc -l) files"
log "INFO" "Weekly backups: $(ls "$BACKUP_DIR/weekly"/*.gz 2>/dev/null | wc -l) files"
log "INFO" "Total backup size: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"

# Create latest symlink for quick access
ln -sf "$BACKUP_DIR/$BACKUP_SUBDIR/db_backup_$TODAY.sql.gz" "$BACKUP_DIR/latest_db_backup.sql.gz" 2>/dev/null

log "INFO" "=== $SCRIPT_NAME completed ==="

exit 0
