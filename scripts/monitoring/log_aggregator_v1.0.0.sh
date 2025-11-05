#!/bin/bash
# Log Aggregation System v1.0.0
# Centralized log collection, parsing, and analysis
# Part of: Skippy Enhancement Project - TIER 3
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"
AGGREGATED_LOGS="${SKIPPY_BASE}/logs/aggregated"
LOG_INDEX="${AGGREGATED_LOGS}/index.json"

usage() {
    cat <<EOF
Log Aggregation System v1.0.0

USAGE:
    $0 <command> [options]

COMMANDS:
    collect                      Collect logs from all sources
    search <query>               Search aggregated logs
    analyze                      Analyze log patterns
    report                       Generate log analysis report
    tail [source]                Tail logs in real-time
    errors                       Show all errors
    warnings                     Show all warnings
    stats                        Show log statistics
    rotate                       Rotate old logs
    clean                        Clean up old logs

OPTIONS:
    --since <date>               Filter logs since date (YYYY-MM-DD)
    --level <level>              Filter by log level (error, warning, info)
    --source <source>            Filter by log source
    --output <file>              Output to file

EXAMPLES:
    # Collect all logs
    $0 collect

    # Search for keyword
    $0 search "deployment"

    # Show errors from last 7 days
    $0 errors --since 2025-10-28

    # Analyze patterns
    $0 analyze

    # Generate report
    $0 report --output logs_report.md

EOF
    exit 1
}

# Parse options
SINCE=""
LEVEL=""
SOURCE=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since)
            SINCE="$2"
            shift 2
            ;;
        --level)
            LEVEL="$2"
            shift 2
            ;;
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"
QUERY="${2:-}"

mkdir -p "$AGGREGATED_LOGS"

log() {
    echo -e "${BLUE}$1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Log sources
declare -A LOG_SOURCES=(
    ["security"]="${SKIPPY_BASE}/logs/security/audit_trail.log"
    ["alerts"]="${SKIPPY_BASE}/logs/alerts/critical_events.log"
    ["secrets"]="${SKIPPY_BASE}/logs/security/secrets_access.log"
    ["backups"]="${SKIPPY_BASE}/conversations/backup_reports"
    ["deployments"]="${SKIPPY_BASE}/conversations/deployment_reports"
    ["validation"]="${SKIPPY_BASE}/conversations/deployment_validation_reports"
    ["security_reports"]="${SKIPPY_BASE}/conversations/security_reports"
)

# Collect logs from all sources
collect_logs() {
    log "Collecting logs from all sources..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local collection_file="${AGGREGATED_LOGS}/collection_${timestamp}.log"

    > "$collection_file"

    # Collect from each source
    for source in "${!LOG_SOURCES[@]}"; do
        local path="${LOG_SOURCES[$source]}"

        if [ -f "$path" ]; then
            log "  Collecting from: $source"
            echo "=== Source: $source ===" >> "$collection_file"
            tail -1000 "$path" >> "$collection_file" 2>/dev/null || true
            echo >> "$collection_file"
        elif [ -d "$path" ]; then
            log "  Collecting from: $source (directory)"
            echo "=== Source: $source ===" >> "$collection_file"
            find "$path" -name "*.md" -o -name "*.log" -mtime -7 | while read -r file; do
                echo "--- $(basename "$file") ---" >> "$collection_file"
                head -50 "$file" >> "$collection_file" 2>/dev/null || true
            done
            echo >> "$collection_file"
        fi
    done

    # Update index
    update_index "$collection_file" "$timestamp"

    success "Logs collected: $collection_file"
}

# Update log index
update_index() {
    local file="$1"
    local timestamp="$2"

    local error_count=$(grep -ci "error" "$file" 2>/dev/null || echo 0)
    local warning_count=$(grep -ci "warning" "$file" 2>/dev/null || echo 0)
    local size=$(du -h "$file" | cut -f1)

    # Create or update index
    if [ ! -f "$LOG_INDEX" ]; then
        echo '{"collections": []}' > "$LOG_INDEX"
    fi

    local temp=$(mktemp)
    jq --arg ts "$timestamp" \
       --arg file "$(basename "$file")" \
       --arg errors "$error_count" \
       --arg warnings "$warning_count" \
       --arg size "$size" \
       '.collections += [{
           timestamp: $ts,
           file: $file,
           errors: ($errors|tonumber),
           warnings: ($warnings|tonumber),
           size: $size,
           collected: (now|todate)
       }]' "$LOG_INDEX" > "$temp"
    mv "$temp" "$LOG_INDEX"
}

# Search logs
search_logs() {
    local query="$1"

    if [ -z "$query" ]; then
        error "Search query required"
        usage
    fi

    log "Searching for: $query"
    echo

    # Search in collected logs
    local found=0

    find "$AGGREGATED_LOGS" -name "collection_*.log" | sort -r | while read -r logfile; do
        local matches=$(grep -i "$query" "$logfile" 2>/dev/null || true)

        if [ -n "$matches" ]; then
            echo -e "${CYAN}=== $(basename "$logfile") ===${NC}"
            echo "$matches" | head -20
            echo
            ((found++))
        fi
    done

    if [ $found -eq 0 ]; then
        warning "No matches found"
    fi
}

# Analyze log patterns
analyze_logs() {
    log "Analyzing log patterns..."
    echo

    local latest_collection=$(find "$AGGREGATED_LOGS" -name "collection_*.log" -type f | sort -r | head -1)

    if [ -z "$latest_collection" ]; then
        warning "No collected logs found. Run: $0 collect"
        exit 1
    fi

    # Error analysis
    echo -e "${CYAN}Error Analysis:${NC}"
    local total_errors=$(grep -ci "error" "$latest_collection" 2>/dev/null || echo 0)
    echo "  Total errors: $total_errors"

    if [ "$total_errors" -gt 0 ]; then
        echo "  Top error messages:"
        grep -i "error" "$latest_collection" | sed 's/.*ERROR://' | sort | uniq -c | sort -rn | head -5 | sed 's/^/    /'
    fi
    echo

    # Warning analysis
    echo -e "${CYAN}Warning Analysis:${NC}"
    local total_warnings=$(grep -ci "warning" "$latest_collection" 2>/dev/null || echo 0)
    echo "  Total warnings: $total_warnings"

    if [ "$total_warnings" -gt 0 ]; then
        echo "  Top warning messages:"
        grep -i "warning" "$latest_collection" | sed 's/.*WARNING://' | sort | uniq -c | sort -rn | head -5 | sed 's/^/    /'
    fi
    echo

    # Activity analysis
    echo -e "${CYAN}Activity Analysis:${NC}"

    local deployments=$(grep -ci "deployment" "$latest_collection" 2>/dev/null || echo 0)
    local backups=$(grep -ci "backup" "$latest_collection" 2>/dev/null || echo 0)
    local security=$(grep -ci "security" "$latest_collection" 2>/dev/null || echo 0)

    echo "  Deployments: $deployments"
    echo "  Backups: $backups"
    echo "  Security events: $security"
    echo

    # Timeline
    echo -e "${CYAN}Recent Activity Timeline:${NC}"
    grep -E "\[.*\]" "$latest_collection" | tail -10 | sed 's/^/  /'
}

# Generate report
generate_report() {
    log "Generating log analysis report..."

    local output="${OUTPUT:-${SKIPPY_BASE}/conversations/log_analysis_$(date +%Y%m%d_%H%M%S).md}"

    cat > "$output" <<EOF
# Log Analysis Report

**Generated:** $(date)
**Aggregation System:** v1.0.0

---

## Summary

EOF

    # Get stats
    local latest_collection=$(find "$AGGREGATED_LOGS" -name "collection_*.log" -type f | sort -r | head -1)

    if [ -n "$latest_collection" ]; then
        local total_lines=$(wc -l < "$latest_collection")
        local total_errors=$(grep -ci "error" "$latest_collection" 2>/dev/null || echo 0)
        local total_warnings=$(grep -ci "warning" "$latest_collection" 2>/dev/null || echo 0)

        cat >> "$output" <<EOF
- Total log entries: $total_lines
- Total errors: $total_errors
- Total warnings: $total_warnings
- Collection period: Last 7 days

## Error Details

$(grep -i "error" "$latest_collection" | head -20 || echo "No errors found")

## Warning Details

$(grep -i "warning" "$latest_collection" | head -20 || echo "No warnings found")

## Recommendations

EOF

        # Add recommendations
        if [ "$total_errors" -gt 100 ]; then
            echo "- ⚠ High error rate detected - investigate root causes" >> "$output"
        fi

        if [ "$total_warnings" -gt 50 ]; then
            echo "- ⚠ Many warnings detected - review and address" >> "$output"
        fi

        if [ "$total_errors" -eq 0 ] && [ "$total_warnings" -eq 0 ]; then
            echo "- ✓ System operating cleanly" >> "$output"
        fi
    else
        echo "No collected logs available" >> "$output"
    fi

    cat >> "$output" <<EOF

---

*Report generated by Log Aggregator v1.0.0*

EOF

    success "Report generated: $output"
}

# Show errors
show_errors() {
    log "Showing errors..."
    echo

    local latest_collection=$(find "$AGGREGATED_LOGS" -name "collection_*.log" -type f | sort -r | head -1)

    if [ -z "$latest_collection" ]; then
        warning "No collected logs. Run: $0 collect"
        exit 1
    fi

    grep -i "error" "$latest_collection" | tail -50
}

# Show warnings
show_warnings() {
    log "Showing warnings..."
    echo

    local latest_collection=$(find "$AGGREGATED_LOGS" -name "collection_*.log" -type f | sort -r | head -1)

    if [ -z "$latest_collection" ]; then
        warning "No collected logs. Run: $0 collect"
        exit 1
    fi

    grep -i "warning" "$latest_collection" | tail -50
}

# Show statistics
show_stats() {
    log "Log Statistics"
    echo

    # Collections
    local total_collections=$(find "$AGGREGATED_LOGS" -name "collection_*.log" | wc -l)
    echo "Total collections: $total_collections"

    # Latest collection stats
    local latest=$(find "$AGGREGATED_LOGS" -name "collection_*.log" -type f | sort -r | head -1)

    if [ -n "$latest" ]; then
        echo
        echo "Latest collection: $(basename "$latest")"
        echo "  Size: $(du -h "$latest" | cut -f1)"
        echo "  Lines: $(wc -l < "$latest")"
        echo "  Errors: $(grep -ci "error" "$latest" 2>/dev/null || echo 0)"
        echo "  Warnings: $(grep -ci "warning" "$latest" 2>/dev/null || echo 0)"
    fi

    # Disk usage
    echo
    echo "Disk usage:"
    du -sh "$AGGREGATED_LOGS"

    # Log sources
    echo
    echo "Active log sources:"
    for source in "${!LOG_SOURCES[@]}"; do
        local path="${LOG_SOURCES[$source]}"
        if [ -f "$path" ] || [ -d "$path" ]; then
            echo "  ✓ $source"
        else
            echo "  ✗ $source (not found)"
        fi
    done
}

# Tail logs
tail_logs() {
    local source="$1"

    if [ -z "$source" ]; then
        # Tail latest collection
        local latest=$(find "$AGGREGATED_LOGS" -name "collection_*.log" -type f | sort -r | head -1)
        if [ -n "$latest" ]; then
            tail -f "$latest"
        else
            warning "No logs to tail"
        fi
    else
        # Tail specific source
        local path="${LOG_SOURCES[$source]}"
        if [ -f "$path" ]; then
            tail -f "$path"
        else
            error "Log source not found: $source"
            exit 1
        fi
    fi
}

# Rotate logs
rotate_logs() {
    log "Rotating old logs..."

    # Move old collections to archive
    local archive_dir="${AGGREGATED_LOGS}/archive"
    mkdir -p "$archive_dir"

    find "$AGGREGATED_LOGS" -name "collection_*.log" -mtime +30 -exec mv {} "$archive_dir/" \;

    # Compress archived logs
    find "$archive_dir" -name "*.log" -type f ! -name "*.gz" -exec gzip {} \;

    success "Log rotation complete"
}

# Clean up old logs
clean_logs() {
    log "Cleaning up old logs..."

    # Delete archived logs older than 90 days
    find "${AGGREGATED_LOGS}/archive" -name "*.gz" -mtime +90 -delete

    # Delete old reports
    find "${SKIPPY_BASE}/conversations" -name "log_analysis_*.md" -mtime +30 -delete

    success "Cleanup complete"
}

# Main command dispatcher
case "$COMMAND" in
    collect)
        collect_logs
        ;;
    search)
        search_logs "$QUERY"
        ;;
    analyze)
        analyze_logs
        ;;
    report)
        generate_report
        ;;
    errors)
        show_errors
        ;;
    warnings)
        show_warnings
        ;;
    stats)
        show_stats
        ;;
    tail)
        tail_logs "$QUERY"
        ;;
    rotate)
        rotate_logs
        ;;
    clean)
        clean_logs
        ;;
    *)
        usage
        ;;
esac

exit 0
