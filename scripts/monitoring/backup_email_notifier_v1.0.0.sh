#!/bin/bash
# Backup Email Notification Script
# Sends email alerts for backup status

EMAIL="eboncorp@gmail.com"
HOSTNAME=$(hostname)

send_notification() {
    local SUBJECT="$1"
    local MESSAGE="$2"
    local PRIORITY="$3"  # normal, high, low

    # Create email content
    cat << EOF | mail -s "[$HOSTNAME] $SUBJECT" "$EMAIL"
$MESSAGE

--
Sent from $HOSTNAME backup monitoring system
Time: $(date)
System: $(uname -a)
EOF

    if [ $? -eq 0 ]; then
        echo "Email notification sent successfully"
        return 0
    else
        echo "Failed to send email notification"
        return 1
    fi
}

check_backup_status() {
    local BACKUP_DATE=$(date +%Y-%m-%d)
    local BACKUP_PATH="googledrive:Backups/ebonhawk-full/$BACKUP_DATE"
    local LOG_FILE="/home/dave/.backup_logs/gdrive_backup_$(date +%Y%m%d).log"

    # Check if backup exists
    if ! rclone lsd "$BACKUP_PATH" >/dev/null 2>&1; then
        send_notification "Backup FAILED - No backup found" \
            "ERROR: No backup found for $BACKUP_DATE

Expected location: $BACKUP_PATH

Please check the backup system immediately.

Log file: $LOG_FILE" "high"
        return 1
    fi

    # Get backup statistics
    BACKUP_INFO=$(rclone size "$BACKUP_PATH" --json 2>/dev/null)
    if [ $? -eq 0 ]; then
        FILES=$(echo "$BACKUP_INFO" | jq -r '.count // 0')
        BYTES=$(echo "$BACKUP_INFO" | jq -r '.bytes // 0')
        SIZE_HUMAN=$(numfmt --to=iec $BYTES)

        # Check for minimum thresholds
        MIN_FILES=100
        MIN_SIZE=52428800  # 50MB

        if [ "$FILES" -lt "$MIN_FILES" ] || [ "$BYTES" -lt "$MIN_SIZE" ]; then
            send_notification "Backup WARNING - Incomplete backup detected" \
                "WARNING: Backup appears incomplete for $BACKUP_DATE

Statistics:
- Files: $FILES (minimum: $MIN_FILES)
- Size: $SIZE_HUMAN (minimum: $(numfmt --to=iec $MIN_SIZE))

This may indicate a partial backup failure.

Log file: $LOG_FILE" "high"
            return 1
        fi

        # Check if backup is recent (within last 2 days)
        CUTOFF_DATE=$(date -d "2 days ago" +%Y-%m-%d)
        if [[ "$BACKUP_DATE" < "$CUTOFF_DATE" ]]; then
            send_notification "Backup WARNING - Stale backup" \
                "WARNING: Latest backup is older than 2 days

Latest backup: $BACKUP_DATE
Current date: $(date +%Y-%m-%d)

Please check the backup system.

Log file: $LOG_FILE" "high"
            return 1
        fi

        # Success notification (optional - only on request)
        if [ "$1" = "--success" ]; then
            send_notification "Backup SUCCESS" \
                "Backup completed successfully for $BACKUP_DATE

Statistics:
- Files backed up: $FILES
- Total size: $SIZE_HUMAN
- Location: $BACKUP_PATH

Google Drive status:
$(rclone about googledrive: --json 2>/dev/null | jq -r '\"Used: \" + (.used|tonumber/1024/1024/1024|floor|tostring) + \"GB / \" + (.total|tonumber/1024/1024/1024|floor|tostring) + \"GB\"' || echo 'Status unavailable')

Log file: $LOG_FILE" "normal"
        fi

        return 0
    else
        send_notification "Backup ERROR - Cannot verify backup" \
            "ERROR: Unable to verify backup for $BACKUP_DATE

Could not retrieve backup statistics from:
$BACKUP_PATH

This may indicate:
- Google Drive connectivity issues
- Rclone configuration problems
- Backup process failure

Log file: $LOG_FILE" "high"
        return 1
    fi
}

send_test_email() {
    send_notification "Backup System TEST" \
        "This is a test email from the backup monitoring system.

If you receive this email, notifications are working correctly.

System information:
- Hostname: $HOSTNAME
- User: $(whoami)
- Date: $(date)
- Uptime: $(uptime)

Backup scripts location: /home/dave/Scripts/
Log files location: /home/dave/.backup_logs/" "normal"
}

case "${1:-check}" in
    "check")
        check_backup_status "$2"
        ;;
    "test")
        send_test_email
        ;;
    "success")
        check_backup_status "--success"
        ;;
    "failure")
        send_notification "Backup FAILED - Manual notification" \
            "${2:-Manual backup failure notification}

Please check the backup system immediately.

Log files: /home/dave/.backup_logs/" "high"
        ;;
    *)
        echo "Usage: $0 [check|test|success|failure] [message]"
        echo ""
        echo "Commands:"
        echo "  check     - Check backup status and send alert if problems found"
        echo "  test      - Send test email"
        echo "  success   - Check status and send success notification"
        echo "  failure   - Send failure notification with optional message"
        exit 1
        ;;
esac