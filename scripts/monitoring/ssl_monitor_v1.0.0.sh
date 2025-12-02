#!/bin/bash
# ssl_monitor_v1.0.0.sh
# Monitor SSL certificate expiration for domains
#
# Usage:
#   ssl_monitor_v1.0.0.sh                  # Check all configured domains
#   ssl_monitor_v1.0.0.sh rundaverun.org   # Check specific domain
#
# Features:
#   - Checks certificate expiration
#   - Warns at configurable thresholds (30, 14, 7 days)
#   - Desktop notifications
#   - Logs to file
#
# Cron: 0 8 * * * /home/dave/skippy/scripts/monitoring/ssl_monitor_v1.0.0.sh
#
# Dependencies:
#   - openssl
#   - notify-send (optional)
#
# Created: 2025-12-01

set -euo pipefail

# Configuration
LOG_DIR="/home/dave/skippy/logs/ssl"
LOG_FILE="$LOG_DIR/ssl_monitor.log"
WARN_DAYS_CRITICAL=7
WARN_DAYS_HIGH=14
WARN_DAYS_MEDIUM=30

# Default domains to check
DEFAULT_DOMAINS=(
    "rundaverun.org"
    "www.rundaverun.org"
)

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE"
    if [[ "$level" == "ERROR" ]] || [[ "$level" == "WARN" ]]; then
        echo "[$level] $message" >&2
    fi
}

# Notification function
notify() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"

    # Desktop notification
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u "$urgency" "$title" "$message" 2>/dev/null || true
    fi

    log "NOTIFY" "$title: $message"
}

# Check SSL certificate
check_ssl() {
    local domain="$1"
    local port="${2:-443}"

    # Get certificate expiration date
    local expiry_date
    expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

    if [[ -z "$expiry_date" ]]; then
        echo "ERROR:Could not retrieve certificate for $domain"
        return 1
    fi

    # Convert to epoch
    local expiry_epoch
    expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
    local now_epoch
    now_epoch=$(date +%s)

    # Calculate days until expiration
    local days_left
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

    # Determine status
    local status
    if [[ $days_left -le 0 ]]; then
        status="EXPIRED"
    elif [[ $days_left -le $WARN_DAYS_CRITICAL ]]; then
        status="CRITICAL"
    elif [[ $days_left -le $WARN_DAYS_HIGH ]]; then
        status="HIGH"
    elif [[ $days_left -le $WARN_DAYS_MEDIUM ]]; then
        status="MEDIUM"
    else
        status="OK"
    fi

    echo "$status:$days_left:$expiry_date"
}

# Main
log "INFO" "=== SSL Certificate Check Started ==="

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SSL CERTIFICATE MONITOR v1.0.0                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Determine domains to check
if [[ $# -gt 0 ]]; then
    DOMAINS=("$@")
else
    DOMAINS=("${DEFAULT_DOMAINS[@]}")
fi

# Initialize counters
TOTAL_CHECKED=0
ISSUES_FOUND=0

printf "%-30s %-12s %-8s %s\n" "DOMAIN" "STATUS" "DAYS" "EXPIRES"
echo "────────────────────────────────────────────────────────────────"

for domain in "${DOMAINS[@]}"; do
    TOTAL_CHECKED=$((TOTAL_CHECKED + 1))

    result=$(check_ssl "$domain")

    if [[ "$result" == ERROR:* ]]; then
        error_msg="${result#ERROR:}"
        printf "%-30s %-12s %-8s %s\n" "$domain" "❌ ERROR" "-" "$error_msg"
        log "ERROR" "$domain: $error_msg"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        continue
    fi

    status="${result%%:*}"
    remaining="${result#*:}"
    days="${remaining%%:*}"
    expiry="${remaining#*:}"

    case "$status" in
        EXPIRED)
            printf "%-30s %-12s %-8s %s\n" "$domain" "🔴 EXPIRED" "$days" "$expiry"
            notify "SSL EXPIRED" "$domain certificate has EXPIRED!" "critical"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            log "ERROR" "$domain: EXPIRED (expired $expiry)"
            ;;
        CRITICAL)
            printf "%-30s %-12s %-8s %s\n" "$domain" "🔴 CRITICAL" "$days" "$expiry"
            notify "SSL Critical" "$domain expires in $days days!" "critical"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            log "WARN" "$domain: expires in $days days (CRITICAL)"
            ;;
        HIGH)
            printf "%-30s %-12s %-8s %s\n" "$domain" "🟠 HIGH" "$days" "$expiry"
            notify "SSL Warning" "$domain expires in $days days" "normal"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            log "WARN" "$domain: expires in $days days (HIGH)"
            ;;
        MEDIUM)
            printf "%-30s %-12s %-8s %s\n" "$domain" "🟡 MEDIUM" "$days" "$expiry"
            log "INFO" "$domain: expires in $days days (MEDIUM)"
            ;;
        OK)
            printf "%-30s %-12s %-8s %s\n" "$domain" "✅ OK" "$days" "$expiry"
            log "INFO" "$domain: OK - expires in $days days"
            ;;
    esac
done

echo ""
echo "────────────────────────────────────────────────────────────────"
echo "Checked: $TOTAL_CHECKED domains"

if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo "Status: ✅ All certificates healthy"
else
    echo "Status: ⚠️  $ISSUES_FOUND issue(s) found"
fi

echo ""
echo "Log: $LOG_FILE"

log "INFO" "Checked $TOTAL_CHECKED domains, $ISSUES_FOUND issues"
log "INFO" "=== SSL Certificate Check Complete ==="

exit $([[ $ISSUES_FOUND -eq 0 ]] && echo 0 || echo 1)
