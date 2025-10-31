#!/bin/bash
# Google Drive Backup Script for Ebonhawk
# Backs up important directories to Google Drive

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
GDRIVE_BACKUP_DIR="googledrive:Backups/ebonhawk"
LOG_FILE="/home/dave/.backup_log"

echo "Starting backup to Google Drive - $BACKUP_DATE" | tee -a $LOG_FILE

# Create backup directory structure
rclone mkdir "$GDRIVE_BACKUP_DIR/$BACKUP_DATE" 2>&1 | tee -a $LOG_FILE

# Backup important directories
echo "Backing up Documents..." | tee -a $LOG_FILE
rclone sync /home/dave/Documents "$GDRIVE_BACKUP_DIR/$BACKUP_DATE/Documents" \
    --exclude "*.tmp" --exclude ".~*" --progress 2>&1 | tee -a $LOG_FILE

echo "Backing up Scans..." | tee -a $LOG_FILE
rclone sync /home/dave/Scans "$GDRIVE_BACKUP_DIR/$BACKUP_DATE/Scans" \
    --progress 2>&1 | tee -a $LOG_FILE

echo "Backing up Scripts..." | tee -a $LOG_FILE
rclone sync /home/dave/Scripts "$GDRIVE_BACKUP_DIR/$BACKUP_DATE/Scripts" \
    --progress 2>&1 | tee -a $LOG_FILE

echo "Backing up Utilities..." | tee -a $LOG_FILE
rclone sync /home/dave/Utilities "$GDRIVE_BACKUP_DIR/$BACKUP_DATE/Utilities" \
    --progress 2>&1 | tee -a $LOG_FILE

echo "Backing up Config..." | tee -a $LOG_FILE
rclone sync /home/dave/Config "$GDRIVE_BACKUP_DIR/$BACKUP_DATE/Config" \
    --progress 2>&1 | tee -a $LOG_FILE

# Keep only last 7 backups to save space
echo "Cleaning old backups..." | tee -a $LOG_FILE
rclone lsf "$GDRIVE_BACKUP_DIR" --dirs-only | sort | head -n -7 | while read old_backup; do
    if [ ! -z "$old_backup" ]; then
        echo "Removing old backup: $old_backup" | tee -a $LOG_FILE
        rclone purge "$GDRIVE_BACKUP_DIR/$old_backup" 2>&1 | tee -a $LOG_FILE
    fi
done

echo "Backup completed at $(date)" | tee -a $LOG_FILE