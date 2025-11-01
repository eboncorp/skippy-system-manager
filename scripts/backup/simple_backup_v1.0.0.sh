#\!/bin/bash
# Simple NexusController Backup Script

BACKUP_DIR="/home/ebon/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

echo "=== NexusController Backup Started ==="
echo "Timestamp: $(date)"
echo "Backup location: $BACKUP_PATH"

# Create backup directory
mkdir -p "$BACKUP_PATH/media_data"
mkdir -p "$BACKUP_PATH/configs"

echo ""
echo "Backing up media data..."

# Backup media service data
for service in jellyfin-config jellyfin-cache homeassistant nodered_data mosquitto; do
    if [ -d "/home/ebon/$service" ]; then
        echo "  ✓ Backing up $service..."
        sudo tar -czf "$BACKUP_PATH/media_data/${service}.tar.gz" -C "/home/ebon" "$service"
        size=$(du -h "$BACKUP_PATH/media_data/${service}.tar.gz" | cut -f1)
        echo "    Created: ${service}.tar.gz ($size)"
    else
        echo "  ✗ Directory not found: /home/ebon/$service"
    fi
done

echo ""
echo "Backing up NexusController configuration..."

# Backup NexusController files
nexus_files="nexus_media_server.py enhanced_simple_server.py simple_nexus_server.py media_service_monitor.py config-media.yaml docker-compose.media.yml Dockerfile requirements.txt nexus-media-monitor.service"

for file in $nexus_files; do
    if [ -f "/home/ebon/$file" ]; then
        cp "/home/ebon/$file" "$BACKUP_PATH/configs/"
        echo "  ✓ Copied: $file"
    fi
done

# Create backup summary
total_size=$(du -sh "$BACKUP_PATH" | cut -f1)
file_count=$(find "$BACKUP_PATH" -type f | wc -l)

cat > "$BACKUP_PATH/backup_info.txt" << EOL
NexusController Backup Summary
==============================
Backup Date: $(date)
Backup Path: $BACKUP_PATH
Total Size: $total_size
Files Backed Up: $file_count

Media Data:
$(ls -lh $BACKUP_PATH/media_data/ 2>/dev/null || echo "No media data backups")

Configuration Files:
$(ls -la $BACKUP_PATH/configs/ 2>/dev/null || echo "No config backups")
EOL

echo ""
echo "=== Backup Completed ==="
echo "Total size: $total_size"
echo "Files backed up: $file_count"
echo "Backup saved to: $BACKUP_PATH"

# Cleanup old backups (keep last 10)
echo ""
echo "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -1t | grep "^backup_" | tail -n +11 | xargs -r rm -rf
remaining=$(ls -1 | grep "^backup_" | wc -l)
echo "Keeping $remaining most recent backups"

echo ""
echo "=== Backup Process Complete ==="

# Check if backup was successful and send notification if failed
if [ ! -d "$BACKUP_PATH" ] || [ "$file_count" -eq 0 ]; then
    echo "[ERROR] Backup failed at $(date)" >> /home/ebon/monitor_alerts.log
    # Uncomment to enable email alerts:
    echo "Backup failed at $(date). Check backup logs for details" | mail -s "Backup Failure Alert" eboncorp@gmail.com
    exit 1
fi
