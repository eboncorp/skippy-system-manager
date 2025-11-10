#!/bin/bash
# Protocol Metrics Analytics
# Version: 1.0.0
# Purpose: Collect and analyze protocol compliance metrics over time
# Usage: bash protocol_metrics_v1.0.0.sh [collect|analyze|trends|export]

VERSION="1.0.0"
COMMAND="${1:-analyze}"
METRICS_DB="/home/dave/skippy/logs/protocol_metrics.db"
WORK_BASE="/home/dave/skippy/work"
AUDIT_DB="/home/dave/skippy/logs/audit_trail.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Initialize metrics database
initialize_db() {
    if [ ! -f "$METRICS_DB" ]; then
        mkdir -p "$(dirname "$METRICS_DB")"

        sqlite3 "$METRICS_DB" <<EOF
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collected_at TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    category TEXT,
    notes TEXT
);

CREATE TABLE daily_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT UNIQUE NOT NULL,
    total_sessions INTEGER,
    compliant_sessions INTEGER,
    compliance_rate REAL,
    tmp_violations INTEGER,
    missing_verification INTEGER,
    missing_documentation INTEGER,
    fact_check_failures INTEGER,
    total_changes INTEGER,
    unique_posts_modified INTEGER
);

CREATE INDEX idx_collected_at ON metrics(collected_at);
CREATE INDEX idx_metric_name ON metrics(metric_name);
CREATE INDEX idx_snapshot_date ON daily_snapshots(snapshot_date);
EOF
        echo "✅ Metrics database initialized"
    fi
}

# Collect current metrics
collect_metrics() {
    echo -e "${BLUE}=== Collecting Protocol Metrics ===${NC}"
    echo "Timestamp: $(date)"
    echo ""

    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")

    # Count sessions in different time periods
    local sessions_today=$(find "$WORK_BASE" -type d -name "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]_*" -mtime 0 2>/dev/null | wc -l)
    local sessions_week=$(find "$WORK_BASE" -type d -name "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]_*" -mtime -7 2>/dev/null | wc -l)
    local sessions_month=$(find "$WORK_BASE" -type d -name "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]_*" -mtime -30 2>/dev/null | wc -l)

    # Compliance metrics
    local total_sessions=0
    local compliant_sessions=0
    local tmp_violations=0
    local missing_verification=0
    local missing_documentation=0

    while IFS= read -r session; do
        ((total_sessions++))

        local violations=0

        # Check /tmp/ usage
        if find "$session" -type f -exec grep -l "/tmp/" {} \; 2>/dev/null | grep -q .; then
            ((tmp_violations++))
            violations=1
        fi

        # Check verification
        local before_count=$(find "$session" -name "*_before.*" 2>/dev/null | wc -l)
        local after_count=$(find "$session" -name "*_after.*" 2>/dev/null | wc -l)
        if [ $before_count -eq 0 ] || [ $after_count -eq 0 ]; then
            ((missing_verification++))
            violations=1
        fi

        # Check documentation
        if [ ! -f "$session/README.md" ]; then
            ((missing_documentation++))
            violations=1
        fi

        if [ $violations -eq 0 ]; then
            ((compliant_sessions++))
        fi

    done < <(find "$WORK_BASE" -type d -name "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]_*" -mtime -30 2>/dev/null)

    # Calculate compliance rate
    local compliance_rate=0
    if [ $total_sessions -gt 0 ]; then
        compliance_rate=$(echo "scale=2; $compliant_sessions * 100 / $total_sessions" | bc)
    fi

    # Audit database metrics
    local total_changes=0
    local unique_posts=0
    if [ -f "$AUDIT_DB" ]; then
        total_changes=$(sqlite3 "$AUDIT_DB" "SELECT COUNT(*) FROM audit_log WHERE timestamp >= datetime('now', '-30 days')" 2>/dev/null || echo "0")
        unique_posts=$(sqlite3 "$AUDIT_DB" "SELECT COUNT(DISTINCT post_id) FROM audit_log WHERE timestamp >= datetime('now', '-30 days') AND post_id IS NOT NULL" 2>/dev/null || echo "0")
    fi

    echo "Sessions (today/week/month): $sessions_today / $sessions_week / $sessions_month"
    echo "Total sessions (30 days): $total_sessions"
    echo "Compliant sessions: $compliant_sessions"
    echo "Compliance rate: ${compliance_rate}%"
    echo "Violations:"
    echo "  - /tmp/ usage: $tmp_violations"
    echo "  - Missing verification: $missing_verification"
    echo "  - Missing documentation: $missing_documentation"
    echo "Total changes: $total_changes"
    echo "Unique posts modified: $unique_posts"
    echo ""

    # Store in database
    sqlite3 "$METRICS_DB" <<EOF
INSERT INTO metrics (collected_at, metric_name, metric_value, metric_unit, category)
VALUES
    ('$timestamp', 'sessions_today', $sessions_today, 'count', 'activity'),
    ('$timestamp', 'sessions_week', $sessions_week, 'count', 'activity'),
    ('$timestamp', 'sessions_month', $sessions_month, 'count', 'activity'),
    ('$timestamp', 'compliance_rate', $compliance_rate, 'percent', 'compliance'),
    ('$timestamp', 'tmp_violations', $tmp_violations, 'count', 'violations'),
    ('$timestamp', 'missing_verification', $missing_verification, 'count', 'violations'),
    ('$timestamp', 'missing_documentation', $missing_documentation, 'count', 'violations'),
    ('$timestamp', 'total_changes', $total_changes, 'count', 'activity'),
    ('$timestamp', 'unique_posts', $unique_posts, 'count', 'activity');

INSERT OR REPLACE INTO daily_snapshots (
    snapshot_date, total_sessions, compliant_sessions, compliance_rate,
    tmp_violations, missing_verification, missing_documentation,
    fact_check_failures, total_changes, unique_posts_modified
) VALUES (
    date('$timestamp'),
    $total_sessions,
    $compliant_sessions,
    $compliance_rate,
    $tmp_violations,
    $missing_verification,
    $missing_documentation,
    0,
    $total_changes,
    $unique_posts
);
EOF

    echo -e "${GREEN}✅ Metrics collected and stored${NC}"
}

# Analyze metrics
analyze_metrics() {
    echo -e "${BLUE}=== Protocol Metrics Analysis ===${NC}"
    echo ""

    # Latest compliance rate
    echo -e "${YELLOW}Current Status:${NC}"
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    printf('  Compliance Rate: %.1f%%', metric_value)
FROM metrics
WHERE metric_name = 'compliance_rate'
ORDER BY collected_at DESC
LIMIT 1;
EOF

    # Average compliance over last 7 days
    echo ""
    echo -e "${YELLOW}7-Day Average:${NC}"
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    printf('  Compliance Rate: %.1f%%', AVG(metric_value))
FROM metrics
WHERE metric_name = 'compliance_rate'
    AND collected_at >= datetime('now', '-7 days');
EOF

    # Trend analysis
    echo ""
    echo -e "${YELLOW}30-Day Trend:${NC}"
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    printf('  %s: %.1f%%', strftime('%Y-%m-%d', collected_at), metric_value)
FROM metrics
WHERE metric_name = 'compliance_rate'
    AND collected_at >= datetime('now', '-30 days')
ORDER BY collected_at DESC
LIMIT 10;
EOF

    # Violation breakdown
    echo ""
    echo -e "${YELLOW}Current Violations:${NC}"
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    printf('  %s: %d',
        CASE metric_name
            WHEN 'tmp_violations' THEN '/tmp/ usage'
            WHEN 'missing_verification' THEN 'Missing verification'
            WHEN 'missing_documentation' THEN 'Missing documentation'
        END,
        CAST(metric_value AS INTEGER)
    )
FROM metrics
WHERE metric_name IN ('tmp_violations', 'missing_verification', 'missing_documentation')
    AND collected_at = (SELECT MAX(collected_at) FROM metrics)
ORDER BY metric_value DESC;
EOF

    # Activity metrics
    echo ""
    echo -e "${YELLOW}Activity Metrics:${NC}"
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    printf('  Sessions today: %d', CAST(metric_value AS INTEGER))
FROM metrics
WHERE metric_name = 'sessions_today'
ORDER BY collected_at DESC
LIMIT 1;

SELECT
    printf('  Sessions this week: %d', CAST(metric_value AS INTEGER))
FROM metrics
WHERE metric_name = 'sessions_week'
ORDER BY collected_at DESC
LIMIT 1;

SELECT
    printf('  Total changes (30 days): %d', CAST(metric_value AS INTEGER))
FROM metrics
WHERE metric_name = 'total_changes'
ORDER BY collected_at DESC
LIMIT 1;

SELECT
    printf('  Unique posts modified: %d', CAST(metric_value AS INTEGER))
FROM metrics
WHERE metric_name = 'unique_posts'
ORDER BY collected_at DESC
LIMIT 1;
EOF

    echo ""
}

# Show trends
show_trends() {
    echo -e "${BLUE}=== Protocol Compliance Trends ===${NC}"
    echo ""

    # Weekly compliance trend
    echo -e "${YELLOW}Weekly Compliance Trend:${NC}"
    echo ""
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    strftime('%Y-W%W', snapshot_date) as week,
    printf('%.1f%%', AVG(compliance_rate)) as avg_compliance,
    SUM(total_sessions) as sessions
FROM daily_snapshots
WHERE snapshot_date >= date('now', '-90 days')
GROUP BY week
ORDER BY week DESC
LIMIT 12;
EOF

    echo ""
    echo -e "${YELLOW}Monthly Activity Trend:${NC}"
    echo ""
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    strftime('%Y-%m', snapshot_date) as month,
    SUM(total_sessions) as total_sessions,
    SUM(total_changes) as total_changes,
    COUNT(DISTINCT unique_posts_modified) as posts_touched
FROM daily_snapshots
WHERE snapshot_date >= date('now', '-180 days')
GROUP BY month
ORDER BY month DESC
LIMIT 6;
EOF

    echo ""
    echo -e "${YELLOW}Violation Trends (Last 30 Days):${NC}"
    echo ""
    sqlite3 "$METRICS_DB" <<EOF
SELECT
    snapshot_date,
    tmp_violations,
    missing_verification,
    missing_documentation
FROM daily_snapshots
WHERE snapshot_date >= date('now', '-30 days')
ORDER BY snapshot_date DESC
LIMIT 10;
EOF

    echo ""
}

# Export metrics
export_metrics() {
    local output_file="${1:-/home/dave/skippy/conversations/protocol_metrics_$(date +%Y-%m-%d).csv}"

    echo -e "${BLUE}=== Exporting Metrics ===${NC}"
    echo "Output: $output_file"
    echo ""

    sqlite3 -header -csv "$METRICS_DB" <<EOF > "$output_file"
SELECT
    snapshot_date,
    total_sessions,
    compliant_sessions,
    compliance_rate,
    tmp_violations,
    missing_verification,
    missing_documentation,
    total_changes,
    unique_posts_modified
FROM daily_snapshots
ORDER BY snapshot_date DESC;
EOF

    if [ -f "$output_file" ]; then
        echo -e "${GREEN}✅ Metrics exported to: $output_file${NC}"
        echo ""
        echo "Rows exported: $(wc -l < "$output_file")"
        echo ""
        echo "You can open this in spreadsheet software for charting and analysis."
    else
        echo -e "${RED}❌ Export failed${NC}"
        exit 1
    fi
}

# Main
initialize_db

case "$COMMAND" in
    collect)
        collect_metrics
        ;;
    analyze)
        analyze_metrics
        ;;
    trends)
        show_trends
        ;;
    export)
        export_metrics "$2"
        ;;
    *)
        echo "Protocol Metrics Analytics v$VERSION"
        echo ""
        echo "Usage: protocol_metrics_v1.0.0.sh [command] [options]"
        echo ""
        echo "Commands:"
        echo "  collect           Collect current metrics"
        echo "  analyze           Analyze collected metrics (default)"
        echo "  trends            Show trends over time"
        echo "  export [file]     Export metrics to CSV"
        echo ""
        echo "Examples:"
        echo "  protocol_metrics_v1.0.0.sh collect"
        echo "  protocol_metrics_v1.0.0.sh analyze"
        echo "  protocol_metrics_v1.0.0.sh trends"
        echo "  protocol_metrics_v1.0.0.sh export /tmp/metrics.csv"
        echo ""
        echo "Database: $METRICS_DB"
        exit 1
        ;;
esac
