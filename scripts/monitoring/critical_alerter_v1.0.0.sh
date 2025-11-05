#!/bin/bash
# Critical Event Alerting System v1.0.0
# Sends alerts for critical events
# Part of: Skippy Enhancement Project - TIER 1
# Created: 2025-11-04

set -euo pipefail

EVENT_TYPE="$1"
EVENT_DETAILS="${2:-No details}"
SKIPPY_BASE="/home/dave/skippy"
ALERT_LOG="${SKIPPY_BASE}/logs/alerts/critical_events.log"
ALERT_EMAIL="${ALERT_EMAIL:-dave@rundaverun.org}"

# Create log directory
mkdir -p "$(dirname "$ALERT_LOG")"

# Log the alert
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] ALERT: $EVENT_TYPE - $EVENT_DETAILS" | tee -a "$ALERT_LOG"

# Determine severity
case "$EVENT_TYPE" in
    "SECURITY_VIOLATION"|"CREDENTIAL_EXPOSURE"|"UNAUTHORIZED_ACCESS")
        SEVERITY="CRITICAL"
        ;;
    "DEPLOYMENT_FAILED"|"BACKUP_FAILED"|"VALIDATION_FAILED")
        SEVERITY="HIGH"
        ;;
    *)
        SEVERITY="MEDIUM"
        ;;
esac

# Create alert message
ALERT_MSG=$(cat <<EOF
CRITICAL ALERT: $EVENT_TYPE

Time: $TIMESTAMP
Severity: $SEVERITY
System: $(hostname)
User: ${USER:-unknown}

Details:
$EVENT_DETAILS

---
This is an automated alert from Skippy Enhancement System.
Review immediately: $ALERT_LOG
EOF
)

# Send email if mail is available
if command -v mail &> /dev/null; then
    echo "$ALERT_MSG" | mail -s "[$SEVERITY] Skippy Alert: $EVENT_TYPE" "$ALERT_EMAIL" 2>/dev/null || true
fi

# Desktop notification if available
if command -v notify-send &> /dev/null; then
    notify-send -u critical "Skippy Alert" "$EVENT_TYPE: $EVENT_DETAILS" 2>/dev/null || true
fi

# Log to syslog if available
if command -v logger &> /dev/null; then
    logger -t skippy-alert -p user.crit "$EVENT_TYPE: $EVENT_DETAILS"
fi

# Write alert file for dashboard
ALERT_FILE="${SKIPPY_BASE}/logs/alerts/active_alert_$(date +%s).alert"
cat > "$ALERT_FILE" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "type": "$EVENT_TYPE",
  "severity": "$SEVERITY",
  "details": "$EVENT_DETAILS",
  "hostname": "$(hostname)",
  "user": "${USER:-unknown}"
}
EOF

echo "Alert sent: $SEVERITY - $EVENT_TYPE"

exit 0
