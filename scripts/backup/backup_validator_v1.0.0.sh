#!/bin/bash
# backup_validator_v1.0.0.sh
# Validate backup integrity and recency
#
# Usage:
#   backup_validator_v1.0.0.sh              # Check all backup locations
#   backup_validator_v1.0.0.sh wordpress    # Check specific type
#
# Features:
#   - Checks backup existence and age
#   - Validates file integrity (checksums, compression)
#   - Reports on backup gaps
#   - Alerts on stale or missing backups
#
# Cron: 0 6 * * * /home/dave/skippy/scripts/backup/backup_validator_v1.0.0.sh
#
# Dependencies:
#   - gzip, tar (for integrity checks)
#   - notify-send (optional)
#
# Created: 2025-12-01

set -euo pipefail

# Configuration
LOG_DIR="/home/dave/skippy/logs/backup"
LOG_FILE="$LOG_DIR/backup_validator.log"

# Backup locations and max age (hours)
declare -A BACKUP_LOCATIONS=(
    ["wordpress"]="/home/dave/skippy/archives/wordpress:168"              # 7 days
    ["database"]="/home/dave/skippy/archives/database:24"                  # 1 day
    ["gdrive"]="/home/dave/skippy/archives/gdrive:168"                    # 7 days
    ["compactions"]="$HOME/.claude/compactions:24"                        # 1 day
)

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging
log() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE"
    if [[ "$level" == "ERROR" ]] || [[ "$level" == "WARN" ]]; then
        echo "[$level] $message" >&2
    fi
}

# Notification
notify() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u "$urgency" "$title" "$message" 2>/dev/null || true
    fi
    log "NOTIFY" "$title: $message"
}

# Check a single backup location
check_backup() {
    local type="$1"
    local config="${BACKUP_LOCATIONS[$type]}"
    local path="${config%%:*}"
    local max_age_hours="${config#*:}"

    if [[ ! -d "$path" ]]; then
        echo "MISSING:$path:Directory does not exist"
        return 1
    fi

    # Find most recent backup file
    local newest_file
    newest_file=$(find "$path" -type f \( -name "*.sql" -o -name "*.sql.gz" -o -name "*.tar.gz" -o -name "*.zip" -o -name "*.json" \) -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    if [[ -z "$newest_file" ]]; then
        echo "EMPTY:$path:No backup files found"
        return 1
    fi

    # Get file age in hours
    local file_mtime
    file_mtime=$(stat -c %Y "$newest_file" 2>/dev/null)
    local now
    now=$(date +%s)
    local age_hours=$(( (now - file_mtime) / 3600 ))

    # Get file size
    local file_size
    file_size=$(stat -c %s "$newest_file" 2>/dev/null)
    local size_human
    size_human=$(numfmt --to=iec-i --suffix=B "$file_size" 2>/dev/null || echo "${file_size}B")

    # Check file integrity
    local integrity="OK"
    if [[ "$newest_file" == *.gz ]]; then
        if ! gzip -t "$newest_file" 2>/dev/null; then
            integrity="CORRUPT"
        fi
    elif [[ "$newest_file" == *.tar.gz ]]; then
        if ! tar -tzf "$newest_file" >/dev/null 2>&1; then
            integrity="CORRUPT"
        fi
    elif [[ "$newest_file" == *.zip ]]; then
        if ! unzip -t "$newest_file" >/dev/null 2>&1; then
            integrity="CORRUPT"
        fi
    fi

    # Determine status
    local status
    if [[ "$integrity" == "CORRUPT" ]]; then
        status="CORRUPT"
    elif [[ $age_hours -gt $max_age_hours ]]; then
        status="STALE"
    elif [[ $file_size -lt 100 ]]; then
        status="SUSPICIOUS"
    else
        status="OK"
    fi

    echo "$status:$newest_file:$age_hours:$max_age_hours:$size_human:$integrity"
}

# Main
log "INFO" "=== Backup Validation Started ==="

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              BACKUP VALIDATOR v1.0.0                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Determine what to check
TYPES_TO_CHECK=()
if [[ $# -gt 0 ]]; then
    TYPES_TO_CHECK=("$@")
else
    TYPES_TO_CHECK=("${!BACKUP_LOCATIONS[@]}")
fi

# Initialize counters
TOTAL_CHECKED=0
ISSUES_FOUND=0

printf "%-12s %-10s %-10s %-10s %-8s %s\n" "TYPE" "STATUS" "AGE(hrs)" "MAX(hrs)" "SIZE" "INTEGRITY"
echo "──────────────────────────────────────────────────────────────────────────"

for type in "${TYPES_TO_CHECK[@]}"; do
    if [[ -z "${BACKUP_LOCATIONS[$type]:-}" ]]; then
        printf "%-12s %-10s\n" "$type" "❓ UNKNOWN"
        continue
    fi

    TOTAL_CHECKED=$((TOTAL_CHECKED + 1))
    result=$(check_backup "$type")

    status="${result%%:*}"
    remaining="${result#*:}"

    case "$status" in
        MISSING)
            path="${remaining%%:*}"
            msg="${remaining#*:}"
            printf "%-12s %-10s %s\n" "$type" "🔴 MISSING" "$msg"
            log "ERROR" "$type: MISSING - $path"
            notify "Backup Missing" "$type backup location missing!" "critical"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            ;;
        EMPTY)
            path="${remaining%%:*}"
            msg="${remaining#*:}"
            printf "%-12s %-10s %s\n" "$type" "🔴 EMPTY" "$msg"
            log "ERROR" "$type: EMPTY - $path"
            notify "Backup Empty" "$type has no backup files!" "critical"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            ;;
        CORRUPT)
            # Parse remaining fields
            IFS=':' read -r file age max_age size integrity <<< "$remaining"
            printf "%-12s %-10s %-10s %-10s %-8s %s\n" "$type" "🔴 CORRUPT" "$age" "$max_age" "$size" "❌ CORRUPT"
            log "ERROR" "$type: CORRUPT - $(basename "$file")"
            notify "Backup Corrupt" "$type backup file is corrupted!" "critical"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            ;;
        STALE)
            IFS=':' read -r file age max_age size integrity <<< "$remaining"
            printf "%-12s %-10s %-10s %-10s %-8s %s\n" "$type" "🟠 STALE" "$age" "$max_age" "$size" "✅ OK"
            log "WARN" "$type: STALE - ${age}h old (max: ${max_age}h)"
            notify "Backup Stale" "$type backup is ${age} hours old (max: ${max_age}h)" "normal"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            ;;
        SUSPICIOUS)
            IFS=':' read -r file age max_age size integrity <<< "$remaining"
            printf "%-12s %-10s %-10s %-10s %-8s %s\n" "$type" "🟡 SMALL" "$age" "$max_age" "$size" "✅ OK"
            log "WARN" "$type: Suspiciously small file ($size)"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            ;;
        OK)
            IFS=':' read -r file age max_age size integrity <<< "$remaining"
            printf "%-12s %-10s %-10s %-10s %-8s %s\n" "$type" "✅ OK" "$age" "$max_age" "$size" "✅ OK"
            log "INFO" "$type: OK - ${age}h old, $size"
            ;;
    esac
done

echo ""
echo "──────────────────────────────────────────────────────────────────────────"
echo "Validated: $TOTAL_CHECKED backup locations"

if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo "Status: ✅ All backups healthy"
else
    echo "Status: ⚠️  $ISSUES_FOUND issue(s) found"
fi

echo ""
echo "Log: $LOG_FILE"

log "INFO" "Validated $TOTAL_CHECKED locations, $ISSUES_FOUND issues"
log "INFO" "=== Backup Validation Complete ==="

exit $([[ $ISSUES_FOUND -eq 0 ]] && echo 0 || echo 1)
