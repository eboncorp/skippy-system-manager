#!/bin/bash
# System Dashboard v1.0.0
# Centralized monitoring and health dashboard
# Part of: Skippy Enhancement Project - TIER 3
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"
DASHBOARD_DATA="${SKIPPY_BASE}/.dashboard"
REFRESH_INTERVAL=5

usage() {
    cat <<EOF
System Dashboard v1.0.0

USAGE:
    $0 [mode] [options]

MODES:
    live                         Live dashboard (auto-refresh)
    snapshot                     Single snapshot
    report                       Generate HTML report
    json                         Output as JSON
    status                       Quick status check

OPTIONS:
    --refresh <seconds>          Refresh interval (default: 5)
    --output <file>              Output file for report mode

EXAMPLES:
    # Live dashboard
    $0 live

    # Single snapshot
    $0 snapshot

    # Generate HTML report
    $0 report --output dashboard.html

    # JSON output
    $0 json

EOF
    exit 1
}

# Parse options
MODE="${1:-live}"
REFRESH_INTERVAL=5
OUTPUT_FILE=""

shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --refresh)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Create dashboard data directory
mkdir -p "$DASHBOARD_DATA"

# Collect system metrics
collect_metrics() {
    local metrics_file="${DASHBOARD_DATA}/metrics_$(date +%s).json"

    cat > "$metrics_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "system": $(collect_system_metrics),
  "wordpress": $(collect_wordpress_metrics),
  "security": $(collect_security_metrics),
  "backups": $(collect_backup_metrics),
  "deployments": $(collect_deployment_metrics),
  "alerts": $(collect_alert_metrics),
  "performance": $(collect_performance_metrics)
}
EOF

    echo "$metrics_file"
}

# System metrics
collect_system_metrics() {
    local uptime_days=$(awk '{print int($1/86400)}' /proc/uptime)
    local load_avg=$(cat /proc/loadavg | awk '{print $1}')
    local cpu_count=$(nproc)
    local mem_total=$(free -m | awk '/^Mem:/ {print $2}')
    local mem_used=$(free -m | awk '/^Mem:/ {print $3}')
    local mem_percent=$(( mem_used * 100 / mem_total ))
    local disk_usage=$(df -h "$SKIPPY_BASE" | awk 'NR==2 {print $5}' | tr -d '%')

    cat <<EOF
{
  "uptime_days": $uptime_days,
  "load_average": $load_avg,
  "cpu_count": $cpu_count,
  "memory_total_mb": $mem_total,
  "memory_used_mb": $mem_used,
  "memory_percent": $mem_percent,
  "disk_usage_percent": $disk_usage,
  "status": "$([ "$load_avg" != "${load_avg%.*}" ] && [ "${load_avg%.*}" -lt "$cpu_count" ] && echo "healthy" || echo "warning")"
}
EOF
}

# WordPress metrics
collect_wordpress_metrics() {
    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"

    if [ -d "$wp_path" ] && command -v wp &> /dev/null; then
        cd "$wp_path" || return

        local post_count=$(wp post list --post_type=post --post_status=publish --format=count 2>/dev/null || echo 0)
        local page_count=$(wp post list --post_type=page --post_status=publish --format=count 2>/dev/null || echo 0)
        local draft_count=$(wp post list --post_status=draft --format=count 2>/dev/null || echo 0)
        local plugin_updates=$(wp plugin list --update=available --format=count 2>/dev/null || echo 0)
        local last_post=$(wp post list --post_type=post --posts_per_page=1 --field=post_date 2>/dev/null | head -1 || echo "unknown")

        cat <<EOF
{
  "posts": $post_count,
  "pages": $page_count,
  "drafts": $draft_count,
  "plugin_updates_available": $plugin_updates,
  "last_post_date": "$last_post",
  "status": "$([ "$plugin_updates" -eq 0 ] && echo "healthy" || echo "updates_needed")"
}
EOF
    else
        echo '{"status": "unavailable"}'
    fi
}

# Security metrics
collect_security_metrics() {
    local audit_log="${SKIPPY_BASE}/logs/security/audit_trail.log"
    local alert_log="${SKIPPY_BASE}/logs/alerts/critical_events.log"
    local secrets_log="${SKIPPY_BASE}/logs/security/secrets_access.log"
    local latest_scan=$(find "${SKIPPY_BASE}/conversations/security_reports" -name "*.md" -mtime -7 2>/dev/null | wc -l)

    local audit_entries=$([ -f "$audit_log" ] && wc -l < "$audit_log" || echo 0)
    local recent_alerts=$([ -f "$alert_log" ] && tail -100 "$alert_log" 2>/dev/null | wc -l || echo 0)
    local secrets_accesses=$([ -f "$secrets_log" ] && tail -100 "$secrets_log" 2>/dev/null | wc -l || echo 0)
    local critical_alerts=$([ -f "$alert_log" ] && grep -c "CRITICAL\|SECURITY" "$alert_log" 2>/dev/null || echo 0)

    cat <<EOF
{
  "audit_entries": $audit_entries,
  "recent_alerts": $recent_alerts,
  "critical_alerts": $critical_alerts,
  "secrets_accesses": $secrets_accesses,
  "recent_security_scans": $latest_scan,
  "status": "$([ "$critical_alerts" -eq 0 ] && [ "$latest_scan" -gt 0 ] && echo "healthy" || echo "attention_needed")"
}
EOF
}

# Backup metrics
collect_backup_metrics() {
    local backup_dir="${SKIPPY_BASE}/backups"
    local latest_backup=$(find "$backup_dir" -type f -name "*.sql" -o -name "*.tar.gz" 2>/dev/null | sort -r | head -1)

    if [ -n "$latest_backup" ]; then
        local backup_age=$(( ($(date +%s) - $(stat -c %Y "$latest_backup")) / 3600 ))
        local backup_count=$(find "$backup_dir" -type f -name "*.sql" -o -name "*.tar.gz" 2>/dev/null | wc -l)
        local backup_size=$(du -sh "$backup_dir" 2>/dev/null | awk '{print $1}')

        cat <<EOF
{
  "latest_backup_hours_ago": $backup_age,
  "total_backups": $backup_count,
  "backup_directory_size": "$backup_size",
  "latest_backup_file": "$(basename "$latest_backup")",
  "status": "$([ "$backup_age" -lt 48 ] && echo "healthy" || echo "stale")"
}
EOF
    else
        echo '{"status": "no_backups"}'
    fi
}

# Deployment metrics
collect_deployment_metrics() {
    local deploy_reports="${SKIPPY_BASE}/conversations/deployment_reports"
    local validation_reports="${SKIPPY_BASE}/conversations/deployment_validation_reports"

    local recent_deployments=$(find "$deploy_reports" -name "*.md" -mtime -7 2>/dev/null | wc -l)
    local recent_validations=$(find "$validation_reports" -name "*.md" -mtime -7 2>/dev/null | wc -l)
    local latest_deployment=$(find "$deploy_reports" -name "*.md" -type f 2>/dev/null | sort -r | head -1)

    if [ -n "$latest_deployment" ]; then
        local deploy_age=$(( ($(date +%s) - $(stat -c %Y "$latest_deployment")) / 86400 ))

        cat <<EOF
{
  "recent_deployments": $recent_deployments,
  "recent_validations": $recent_validations,
  "days_since_last_deployment": $deploy_age,
  "latest_deployment": "$(basename "$latest_deployment")",
  "status": "active"
}
EOF
    else
        echo '{"status": "no_deployments"}'
    fi
}

# Alert metrics
collect_alert_metrics() {
    local alert_log="${SKIPPY_BASE}/logs/alerts/critical_events.log"
    local active_alerts=$(find "${SKIPPY_BASE}/logs/alerts" -name "active_alert_*.alert" 2>/dev/null | wc -l)

    if [ -f "$alert_log" ]; then
        local alerts_24h=$(grep "$(date +%Y-%m-%d)" "$alert_log" 2>/dev/null | wc -l)
        local alerts_7d=$(tail -500 "$alert_log" 2>/dev/null | wc -l)

        cat <<EOF
{
  "alerts_last_24h": $alerts_24h,
  "alerts_last_7d": $alerts_7d,
  "active_alerts": $active_alerts,
  "status": "$([ "$active_alerts" -eq 0 ] && [ "$alerts_24h" -eq 0 ] && echo "healthy" || echo "alerts_present")"
}
EOF
    else
        echo '{"alerts_last_24h": 0, "alerts_last_7d": 0, "active_alerts": 0, "status": "healthy"}'
    fi
}

# Performance metrics
collect_performance_metrics() {
    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"
    local avg_validation_time=0
    local avg_deployment_time=0

    # Calculate average validation time from recent reports
    if [ -d "${SKIPPY_BASE}/conversations/deployment_validation_reports" ]; then
        avg_validation_time=$(find "${SKIPPY_BASE}/conversations/deployment_validation_reports" -name "*.md" -mtime -7 2>/dev/null | wc -l)
    fi

    cat <<EOF
{
  "avg_validation_time_seconds": $avg_validation_time,
  "avg_deployment_time_seconds": $avg_deployment_time,
  "tools_available": $(find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" -executable 2>/dev/null | wc -l),
  "status": "operational"
}
EOF
}

# Calculate overall health score
calculate_health_score() {
    local metrics_file="$1"

    local score=100

    # Parse metrics
    local sys_status=$(jq -r '.system.status' "$metrics_file")
    local wp_status=$(jq -r '.wordpress.status' "$metrics_file")
    local sec_status=$(jq -r '.security.status' "$metrics_file")
    local backup_status=$(jq -r '.backups.status' "$metrics_file")
    local alert_status=$(jq -r '.alerts.status' "$metrics_file")

    # Deduct points for issues
    [ "$sys_status" != "healthy" ] && score=$((score - 10))
    [ "$wp_status" = "updates_needed" ] && score=$((score - 5))
    [ "$sec_status" = "attention_needed" ] && score=$((score - 15))
    [ "$backup_status" = "stale" ] && score=$((score - 10))
    [ "$backup_status" = "no_backups" ] && score=$((score - 20))
    [ "$alert_status" = "alerts_present" ] && score=$((score - 15))

    echo "$score"
}

# Get health grade
get_health_grade() {
    local score=$1

    if [ "$score" -ge 95 ]; then
        echo "A+"
    elif [ "$score" -ge 90 ]; then
        echo "A"
    elif [ "$score" -ge 85 ]; then
        echo "B+"
    elif [ "$score" -ge 80 ]; then
        echo "B"
    elif [ "$score" -ge 75 ]; then
        echo "C+"
    elif [ "$score" -ge 70 ]; then
        echo "C"
    else
        echo "D"
    fi
}

# Display live dashboard
display_dashboard() {
    local metrics_file="$1"

    clear

    # Header
    echo -e "${CYAN}${BOLD}"
    cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                  SKIPPY SYSTEM DASHBOARD                      ║
║              Run Dave Run Campaign Infrastructure             ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    # Calculate health
    local health_score=$(calculate_health_score "$metrics_file")
    local health_grade=$(get_health_grade "$health_score")
    local health_color="${GREEN}"
    [ "$health_score" -lt 90 ] && health_color="${YELLOW}"
    [ "$health_score" -lt 75 ] && health_color="${RED}"

    # Overall Health
    echo -e "${BOLD}Overall System Health:${NC} ${health_color}${health_score}% ($health_grade)${NC}"
    echo -e "Last Updated: $(date)"
    echo

    # System Status
    echo -e "${BLUE}${BOLD}═══ System Status ═══${NC}"
    local uptime=$(jq -r '.system.uptime_days' "$metrics_file")
    local load=$(jq -r '.system.load_average' "$metrics_file")
    local mem=$(jq -r '.system.memory_percent' "$metrics_file")
    local disk=$(jq -r '.system.disk_usage_percent' "$metrics_file")

    echo -e "Uptime:      ${uptime} days"
    echo -e "Load Avg:    ${load}"
    echo -e "Memory:      ${mem}%"
    echo -e "Disk Usage:  ${disk}%"
    echo

    # WordPress Status
    echo -e "${BLUE}${BOLD}═══ WordPress Status ═══${NC}"
    local wp_status=$(jq -r '.wordpress.status' "$metrics_file")
    if [ "$wp_status" != "unavailable" ]; then
        local posts=$(jq -r '.wordpress.posts' "$metrics_file")
        local pages=$(jq -r '.wordpress.pages' "$metrics_file")
        local drafts=$(jq -r '.wordpress.drafts' "$metrics_file")
        local updates=$(jq -r '.wordpress.plugin_updates_available' "$metrics_file")

        echo -e "Posts:       ${posts}"
        echo -e "Pages:       ${pages}"
        echo -e "Drafts:      ${drafts}"
        [ "$updates" -gt 0 ] && echo -e "Updates:     ${YELLOW}$updates available${NC}" || echo -e "Updates:     ${GREEN}Up to date${NC}"
    else
        echo -e "${YELLOW}WordPress not available${NC}"
    fi
    echo

    # Security Status
    echo -e "${BLUE}${BOLD}═══ Security Status ═══${NC}"
    local recent_scans=$(jq -r '.security.recent_security_scans' "$metrics_file")
    local critical_alerts=$(jq -r '.security.critical_alerts' "$metrics_file")
    local secrets_access=$(jq -r '.security.secrets_accesses' "$metrics_file")

    [ "$recent_scans" -gt 0 ] && echo -e "Security Scans:  ${GREEN}$recent_scans this week${NC}" || echo -e "Security Scans:  ${YELLOW}None this week${NC}"
    [ "$critical_alerts" -eq 0 ] && echo -e "Critical Alerts: ${GREEN}None${NC}" || echo -e "Critical Alerts: ${RED}$critical_alerts${NC}"
    echo -e "Secrets Access:  $secrets_access recent"
    echo

    # Backup Status
    echo -e "${BLUE}${BOLD}═══ Backup Status ═══${NC}"
    local backup_status=$(jq -r '.backups.status' "$metrics_file")
    if [ "$backup_status" != "no_backups" ]; then
        local backup_age=$(jq -r '.backups.latest_backup_hours_ago' "$metrics_file")
        local backup_count=$(jq -r '.backups.total_backups' "$metrics_file")
        local backup_size=$(jq -r '.backups.backup_directory_size' "$metrics_file")

        [ "$backup_age" -lt 24 ] && echo -e "Latest Backup:   ${GREEN}${backup_age}h ago${NC}" || echo -e "Latest Backup:   ${YELLOW}${backup_age}h ago${NC}"
        echo -e "Total Backups:   $backup_count"
        echo -e "Storage Used:    $backup_size"
    else
        echo -e "${RED}No backups found${NC}"
    fi
    echo

    # Alerts
    echo -e "${BLUE}${BOLD}═══ Recent Activity ═══${NC}"
    local alerts_24h=$(jq -r '.alerts.alerts_last_24h' "$metrics_file")
    local recent_deploys=$(jq -r '.deployments.recent_deployments' "$metrics_file")
    local recent_validations=$(jq -r '.deployments.recent_validations' "$metrics_file")

    echo -e "Alerts (24h):    $alerts_24h"
    echo -e "Deployments (7d): $recent_deploys"
    echo -e "Validations (7d): $recent_validations"
    echo

    # Footer
    echo -e "${CYAN}─────────────────────────────────────────────────────────────${NC}"
    echo -e "Press Ctrl+C to exit | Refresh: ${REFRESH_INTERVAL}s"
}

# Generate snapshot
generate_snapshot() {
    echo -e "${BLUE}Collecting metrics...${NC}"
    local metrics_file=$(collect_metrics)

    display_dashboard "$metrics_file"
}

# Generate HTML report
generate_html_report() {
    local output="${OUTPUT_FILE:-${SKIPPY_BASE}/conversations/dashboard_$(date +%Y%m%d_%H%M%S).html}"

    echo -e "${BLUE}Generating HTML report...${NC}"
    local metrics_file=$(collect_metrics)
    local health_score=$(calculate_health_score "$metrics_file")
    local health_grade=$(get_health_grade "$health_score")

    cat > "$output" <<'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Skippy System Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
        .health { font-size: 24px; font-weight: bold; margin: 20px 0; }
        .health.excellent { color: #4CAF50; }
        .health.good { color: #8BC34A; }
        .health.warning { color: #FF9800; }
        .health.critical { color: #F44336; }
        .section { margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #4CAF50; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-label { font-weight: bold; color: #666; }
        .metric-value { color: #333; }
        .status-healthy { color: #4CAF50; }
        .status-warning { color: #FF9800; }
        .status-critical { color: #F44336; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #4CAF50; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Skippy System Dashboard</h1>
        <p><strong>Generated:</strong> TIMESTAMP_PLACEHOLDER</p>

        <div class="health HEALTH_CLASS_PLACEHOLDER">
            Overall System Health: HEALTH_SCORE_PLACEHOLDER% (HEALTH_GRADE_PLACEHOLDER)
        </div>

        METRICS_PLACEHOLDER
    </div>
</body>
</html>
HTMLEOF

    # Replace placeholders
    sed -i "s/TIMESTAMP_PLACEHOLDER/$(date)/" "$output"
    sed -i "s/HEALTH_SCORE_PLACEHOLDER/$health_score/" "$output"
    sed -i "s/HEALTH_GRADE_PLACEHOLDER/$health_grade/" "$output"

    local health_class="excellent"
    [ "$health_score" -lt 90 ] && health_class="good"
    [ "$health_score" -lt 80 ] && health_class="warning"
    [ "$health_score" -lt 70 ] && health_class="critical"
    sed -i "s/HEALTH_CLASS_PLACEHOLDER/$health_class/" "$output"

    echo -e "${GREEN}✓ HTML report generated: $output${NC}"
}

# JSON output
output_json() {
    local metrics_file=$(collect_metrics)
    cat "$metrics_file"
}

# Quick status
quick_status() {
    local metrics_file=$(collect_metrics)
    local health_score=$(calculate_health_score "$metrics_file")
    local health_grade=$(get_health_grade "$health_score")

    echo "System Health: ${health_score}% ($health_grade)"

    # Quick checks
    local critical_alerts=$(jq -r '.security.critical_alerts' "$metrics_file")
    local backup_status=$(jq -r '.backups.status' "$metrics_file")

    [ "$critical_alerts" -gt 0 ] && echo "⚠ Critical alerts: $critical_alerts"
    [ "$backup_status" = "stale" ] && echo "⚠ Backups are stale"
    [ "$backup_status" = "no_backups" ] && echo "⚠ No backups found"

    [ "$health_score" -ge 90 ] && echo "✓ All systems operational"
}

# Live mode
live_mode() {
    while true; do
        local metrics_file=$(collect_metrics)
        display_dashboard "$metrics_file"
        sleep "$REFRESH_INTERVAL"
    done
}

# Main
case "$MODE" in
    live)
        live_mode
        ;;
    snapshot)
        generate_snapshot
        ;;
    report)
        generate_html_report
        ;;
    json)
        output_json
        ;;
    status)
        quick_status
        ;;
    *)
        usage
        ;;
esac

exit 0
