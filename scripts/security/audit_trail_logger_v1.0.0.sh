#!/bin/bash
# Security Audit Trail Logger v1.0.0
# Logs all security-relevant actions
# Part of: Skippy Enhancement Project - TIER 1
# Created: 2025-11-04

set -euo pipefail

ACTION="$1"
DETAILS="${2:-No details provided}"
USER="${USER:-unknown}"
SKIPPY_BASE="/home/dave/skippy"
AUDIT_LOG="${SKIPPY_BASE}/logs/security/audit_trail.log"
AUDIT_ARCHIVE="${SKIPPY_BASE}/logs/security/audit_archive"

# Create directories
mkdir -p "$(dirname "$AUDIT_LOG")" "$AUDIT_ARCHIVE"

# Rotate log if > 10MB
if [ -f "$AUDIT_LOG" ] && [ "$(stat -f%z "$AUDIT_LOG" 2>/dev/null || stat -c%s "$AUDIT_LOG")" -gt 10485760 ]; then
    mv "$AUDIT_LOG" "${AUDIT_ARCHIVE}/audit_trail_$(date +%Y%m%d_%H%M%S).log"
    gzip "${AUDIT_ARCHIVE}/audit_trail_$(date +%Y%m%d_%H%M%S).log" 2>/dev/null || true
fi

# Log entry
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HOSTNAME=$(hostname)

echo "[$TIMESTAMP] [$USER@$HOSTNAME] [$ACTION] $DETAILS" >> "$AUDIT_LOG"

# Alert on critical actions
case "$ACTION" in
    "SECURITY_VIOLATION"|"UNAUTHORIZED_ACCESS"|"CREDENTIAL_EXPOSURE")
        # Send alert (implement actual alerting in critical_alerter)
        /home/dave/skippy/development/scripts/scripts/monitoring/critical_alerter_v1.0.0.sh "$ACTION" "$DETAILS" 2>/dev/null || true
        ;;
esac

exit 0
