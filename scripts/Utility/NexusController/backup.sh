#!/bin/bash
# NexusController Secure Backup Script

BACKUP_DIR="$HOME/.nexus/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nexus_backup_$DATE.tar.gz"

echo "🔄 Creating NexusController backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup
tar -czf "$BACKUP_FILE" \
    ~/.nexus/config.enc \
    ~/.nexus/logs/ \
    ~/.ssh/id_ed25519* \
    ~/.ssh/config \
    ~/.ssh/known_hosts \
    2>/dev/null

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 10 backups
cd "$BACKUP_DIR" && ls -t nexus_backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "🧹 Old backups cleaned up"
