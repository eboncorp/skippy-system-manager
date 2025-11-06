#!/bin/bash
# Example: WordPress Backup Automation
# This script demonstrates how to use Skippy for WordPress backups

set -euo pipefail

# Load configuration
source ../../config.env

# Run backup
echo "Starting WordPress backup..."
bash ../../scripts/backup/full_home_backup_v1.0.0.sh

# Verify backup
if [ -d "${WORDPRESS_BACKUP_PATH}" ]; then
    echo "Backup completed successfully"
    ls -lh "${WORDPRESS_BACKUP_PATH}"
else
    echo "Backup failed!"
    exit 1
fi

# Optional: Upload to cloud
# rclone sync "${WORDPRESS_BACKUP_PATH}" gdrive:Backups/WordPress
