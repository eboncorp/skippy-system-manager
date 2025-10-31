#!/bin/bash
# Quick backup status checker

echo "================================================"
echo "         Google Drive Backup Status"
echo "================================================"
echo

# Check if backup is currently running
if pgrep -f "full_home_backup.sh" > /dev/null; then
    echo "🔄 BACKUP IS CURRENTLY RUNNING"
    echo

    # Show current progress
    CURRENT_SIZE=$(rclone size "googledrive:Backups/ebonhawk-full/$(date +%Y-%m-%d)" --json 2>/dev/null | jq -r '.bytes // 0')
    CURRENT_FILES=$(rclone size "googledrive:Backups/ebonhawk-full/$(date +%Y-%m-%d)" --json 2>/dev/null | jq -r '.count // 0')

    if [ "$CURRENT_SIZE" -gt 0 ]; then
        echo "Progress so far:"
        echo "  Files uploaded: $CURRENT_FILES"
        echo "  Data uploaded: $(numfmt --to=iec $CURRENT_SIZE)"
        echo

        # Show last few log entries
        echo "Recent activity:"
        tail -5 /home/dave/.backup_logs/gdrive_backup_$(date +%Y%m%d).log 2>/dev/null | sed 's/^/  /'
    fi
else
    echo "✅ No backup currently running"
fi

echo
echo "Google Drive Usage:"
QUOTA_INFO=$(rclone about "googledrive:" --json 2>/dev/null)
if [ $? -eq 0 ]; then
    TOTAL=$(echo "$QUOTA_INFO" | jq -r '.total // 0')
    USED=$(echo "$QUOTA_INFO" | jq -r '.used // 0')
    FREE=$(echo "$QUOTA_INFO" | jq -r '.free // 0')

    if [ "$TOTAL" != "0" ]; then
        PERCENT=$((USED * 100 / TOTAL))
        echo "  Used: $(numfmt --to=iec $USED) / $(numfmt --to=iec $TOTAL) (${PERCENT}%)"
        echo "  Free: $(numfmt --to=iec $FREE)"
    fi
fi

echo
echo "Recent Backups:"
rclone lsd "googledrive:Backups/ebonhawk-full" 2>/dev/null | tail -5 | while read line; do
    DIR_NAME=$(echo "$line" | awk '{print $NF}')
    DIR_SIZE=$(rclone size "googledrive:Backups/ebonhawk-full/$DIR_NAME" --json 2>/dev/null | jq -r '.bytes // 0')
    DIR_FILES=$(rclone size "googledrive:Backups/ebonhawk-full/$DIR_NAME" --json 2>/dev/null | jq -r '.count // 0')

    if [ "$DIR_SIZE" -gt 0 ]; then
        echo "  $DIR_NAME: $(numfmt --to=iec $DIR_SIZE) ($DIR_FILES files)"
    else
        echo "  $DIR_NAME: (empty or in progress)"
    fi
done

echo
echo "Next scheduled backup:"
crontab -l 2>/dev/null | grep "full_home_backup.sh" | sed 's/^/  /'

echo
echo "================================================"
echo "For detailed logs: tail -f /home/dave/.backup_logs/gdrive_backup_$(date +%Y%m%d).log"