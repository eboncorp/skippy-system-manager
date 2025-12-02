#\!/bin/bash
# Google Drive Backup Script for Ebon Server
# Backs up Nexus components and configurations

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
GDRIVE_BACKUP_DIR="Backups/ebon"
LOG_FILE="/home/ebon/backup.log"

echo "Starting Ebon server backup - $BACKUP_DATE" | tee -a $LOG_FILE

# Install rclone if not present
if \! command -v rclone &> /dev/null; then
    echo "Installing rclone..." | tee -a $LOG_FILE
    curl https://rclone.org/install.sh | sudo bash
fi

# Backup Nexus components
echo "Creating backup archive..." | tee -a $LOG_FILE
tar -czf /tmp/nexus_backup_$BACKUP_DATE.tar.gz \
    /home/ebon/nexus*.py \
    /home/ebon/nexus*.log \
    /home/ebon/*.service \
    /home/ebon/docker-compose*.yml 2>/dev/null

# Upload to Google Drive using rclone
echo "Uploading to Google Drive..." | tee -a $LOG_FILE
rclone copy /tmp/nexus_backup_$BACKUP_DATE.tar.gz googledrive:$GDRIVE_BACKUP_DIR/ --progress

# Clean up temp file
rm /tmp/nexus_backup_$BACKUP_DATE.tar.gz

echo "Backup completed at $(date)" | tee -a $LOG_FILE
