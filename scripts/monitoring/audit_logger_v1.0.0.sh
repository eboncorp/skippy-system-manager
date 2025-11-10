#!/bin/bash
# Audit Trail Logger
# Version: 1.0.0
# Purpose: Log all WordPress content changes with full audit trail
# Usage: Source this in other scripts or use directly

VERSION="1.0.0"
AUDIT_LOG="/home/dave/skippy/logs/audit_trail.log"
AUDIT_DB="/home/dave/skippy/logs/audit_trail.db"

# Ensure log directory exists
mkdir -p "$(dirname "$AUDIT_LOG")"

# Initialize SQLite database if it doesn't exist
if [ ! -f "$AUDIT_DB" ]; then
    sqlite3 "$AUDIT_DB" <<EOF
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    post_id INTEGER,
    post_title TEXT,
    post_type TEXT,
    site TEXT,
    user TEXT,
    session_dir TEXT,
    before_hash TEXT,
    after_hash TEXT,
    diff_lines INTEGER,
    fact_check_status TEXT,
    protocol_version TEXT,
    tool_version TEXT,
    notes TEXT
);

CREATE INDEX idx_timestamp ON audit_log(timestamp);
CREATE INDEX idx_post_id ON audit_log(post_id);
CREATE INDEX idx_site ON audit_log(site);
CREATE INDEX idx_action ON audit_log(action);
EOF
fi

# Log action to both file and database
log_audit() {
    local action="$1"
    local post_id="$2"
    local post_title="$3"
    local post_type="$4"
    local site="$5"
    local session_dir="$6"
    local notes="$7"

    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    local user=$(whoami)
    local before_hash=""
    local after_hash=""
    local diff_lines=0
    local fact_check_status="UNKNOWN"

    # Calculate hashes if files exist
    if [ -d "$session_dir" ]; then
        local before_file=$(find "$session_dir" -name "*_before.html" 2>/dev/null | head -1)
        local after_file=$(find "$session_dir" -name "*_after.html" 2>/dev/null | head -1)

        if [ -f "$before_file" ]; then
            before_hash=$(md5sum "$before_file" | cut -d' ' -f1)
        fi

        if [ -f "$after_file" ]; then
            after_hash=$(md5sum "$after_file" | cut -d' ' -f1)
        fi

        # Calculate diff lines
        if [ -f "$before_file" ] && [ -f "$after_file" ]; then
            diff_lines=$(diff "$before_file" "$after_file" | wc -l)
        fi
    fi

    # Write to log file
    echo "$timestamp|$action|$post_id|$post_title|$post_type|$site|$user|$session_dir|$before_hash|$after_hash|$diff_lines|$notes" >> "$AUDIT_LOG"

    # Write to database
    sqlite3 "$AUDIT_DB" <<EOF
INSERT INTO audit_log (
    timestamp, action, post_id, post_title, post_type, site, user,
    session_dir, before_hash, after_hash, diff_lines, fact_check_status,
    protocol_version, tool_version, notes
) VALUES (
    '$timestamp',
    '$action',
    $([[ -n "$post_id" ]] && echo "$post_id" || echo "NULL"),
    '$(echo "$post_title" | sed "s/'/''/g")',
    '$post_type',
    '$site',
    '$user',
    '$session_dir',
    '$before_hash',
    '$after_hash',
    $diff_lines,
    '$fact_check_status',
    'v1.0',
    '$VERSION',
    '$(echo "$notes" | sed "s/'/''/g")'
);
EOF
}

# Query audit log
query_audit() {
    local query_type="$1"
    local param="$2"

    case "$query_type" in
        post)
            sqlite3 "$AUDIT_DB" <<EOF
SELECT timestamp, action, post_title, site, user, notes
FROM audit_log
WHERE post_id = $param
ORDER BY timestamp DESC;
EOF
            ;;
        recent)
            local limit="${param:-10}"
            sqlite3 "$AUDIT_DB" <<EOF
SELECT timestamp, action, post_id, post_title, site, user
FROM audit_log
ORDER BY timestamp DESC
LIMIT $limit;
EOF
            ;;
        site)
            sqlite3 "$AUDIT_DB" <<EOF
SELECT timestamp, action, post_id, post_title, user, notes
FROM audit_log
WHERE site = '$param'
ORDER BY timestamp DESC;
EOF
            ;;
        user)
            sqlite3 "$AUDIT_DB" <<EOF
SELECT timestamp, action, post_id, post_title, site
FROM audit_log
WHERE user = '$param'
ORDER BY timestamp DESC;
EOF
            ;;
        date)
            sqlite3 "$AUDIT_DB" <<EOF
SELECT timestamp, action, post_id, post_title, site, user
FROM audit_log
WHERE date(timestamp) = '$param'
ORDER BY timestamp DESC;
EOF
            ;;
        stats)
            sqlite3 "$AUDIT_DB" <<EOF
SELECT
    action,
    COUNT(*) as count,
    COUNT(DISTINCT post_id) as unique_posts,
    site
FROM audit_log
GROUP BY action, site
ORDER BY count DESC;
EOF
            ;;
        *)
            echo "Unknown query type: $query_type"
            echo "Valid types: post, recent, site, user, date, stats"
            return 1
            ;;
    esac
}

# Generate audit report
generate_audit_report() {
    local output_file="${1:-/home/dave/skippy/conversations/audit_report_$(date +%Y-%m-%d).md}"

    cat > "$output_file" <<EOF
# Audit Trail Report

**Generated:** $(date)
**Period:** Last 30 days
**Tool:** Audit Logger v$VERSION

---

## Summary Statistics

\`\`\`
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT
    'Total Actions: ' || COUNT(*) FROM audit_log
UNION ALL
SELECT
    'Unique Posts Modified: ' || COUNT(DISTINCT post_id) FROM audit_log WHERE post_id IS NOT NULL
UNION ALL
SELECT
    'Local Site Changes: ' || COUNT(*) FROM audit_log WHERE site = 'rundaverun-local'
UNION ALL
SELECT
    'Production Changes: ' || COUNT(*) FROM audit_log WHERE site = 'rundaverun'
UNION ALL
SELECT
    'Average Changes per Day: ' || ROUND(COUNT(*) / 30.0, 1) FROM audit_log
    WHERE timestamp >= datetime('now', '-30 days');
QUERY
)
\`\`\`

---

## Actions by Type

\`\`\`
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT
    printf('%-20s %5d', action, COUNT(*))
FROM audit_log
GROUP BY action
ORDER BY COUNT(*) DESC;
QUERY
)
\`\`\`

---

## Recent Changes (Last 20)

| Timestamp | Action | Post ID | Title | Site |
|-----------|--------|---------|-------|------|
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT
    printf('| %s | %s | %s | %s | %s |',
        timestamp,
        action,
        COALESCE(CAST(post_id AS TEXT), 'N/A'),
        SUBSTR(post_title, 1, 30),
        site
    )
FROM audit_log
ORDER BY timestamp DESC
LIMIT 20;
QUERY
)

---

## Most Frequently Modified Posts

| Post ID | Title | Modifications | Latest |
|---------|-------|---------------|--------|
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT
    printf('| %s | %s | %d | %s |',
        CAST(post_id AS TEXT),
        SUBSTR(post_title, 1, 30),
        COUNT(*),
        MAX(timestamp)
    )
FROM audit_log
WHERE post_id IS NOT NULL
GROUP BY post_id
ORDER BY COUNT(*) DESC
LIMIT 10;
QUERY
)

---

## Changes by Site

\`\`\`
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT
    printf('%-20s %5d', site, COUNT(*))
FROM audit_log
GROUP BY site
ORDER BY COUNT(*) DESC;
QUERY
)
\`\`\`

---

## Data Integrity Checks

\`\`\`
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT 'Changes with verification: ' || COUNT(*)
FROM audit_log
WHERE after_hash IS NOT NULL AND after_hash != ''
UNION ALL
SELECT 'Changes without verification: ' || COUNT(*)
FROM audit_log
WHERE after_hash IS NULL OR after_hash = ''
UNION ALL
SELECT 'Total diff lines changed: ' || SUM(diff_lines)
FROM audit_log
WHERE diff_lines > 0;
QUERY
)
\`\`\`

---

## Protocol Compliance

\`\`\`
$(sqlite3 "$AUDIT_DB" <<QUERY
SELECT
    CASE
        WHEN session_dir != '' THEN 'Sessions with proper directory: '
        ELSE 'Sessions without directory: '
    END || COUNT(*)
FROM audit_log
GROUP BY CASE WHEN session_dir != '' THEN 1 ELSE 0 END;
QUERY
)
\`\`\`

---

**Report Location:** $output_file
**Database:** $AUDIT_DB
**Log File:** $AUDIT_LOG
EOF

    echo "$output_file"
}

# Main CLI
if [ "$0" = "${BASH_SOURCE[0]}" ]; then
    case "$1" in
        log)
            shift
            log_audit "$@"
            echo "✅ Logged to audit trail"
            ;;
        query)
            query_audit "$2" "$3"
            ;;
        report)
            output=$(generate_audit_report "$2")
            echo "✅ Generated: $output"
            ;;
        recent)
            echo "Recent audit entries:"
            query_audit recent "${2:-10}"
            ;;
        post)
            if [ -z "$2" ]; then
                echo "Error: Post ID required"
                exit 1
            fi
            echo "Audit history for Post $2:"
            query_audit post "$2"
            ;;
        stats)
            echo "Audit statistics:"
            query_audit stats
            ;;
        *)
            echo "Audit Trail Logger v$VERSION"
            echo ""
            echo "Usage: audit_logger_v1.0.0.sh [command] [args]"
            echo ""
            echo "Commands:"
            echo "  log <action> <post_id> <title> <type> <site> <session_dir> <notes>"
            echo "      Log an action to the audit trail"
            echo ""
            echo "  query <type> <param>"
            echo "      Query audit log (types: post, recent, site, user, date, stats)"
            echo ""
            echo "  report [output_file]"
            echo "      Generate comprehensive audit report"
            echo ""
            echo "  recent [limit]"
            echo "      Show recent entries (default: 10)"
            echo ""
            echo "  post <post_id>"
            echo "      Show history for specific post"
            echo ""
            echo "  stats"
            echo "      Show statistics"
            echo ""
            echo "Examples:"
            echo "  audit_logger_v1.0.0.sh log UPDATE 105 'Homepage' page rundaverun-local /path/to/session 'Fixed typos'"
            echo "  audit_logger_v1.0.0.sh recent 20"
            echo "  audit_logger_v1.0.0.sh post 105"
            echo "  audit_logger_v1.0.0.sh report"
            echo ""
            echo "Files:"
            echo "  Log: $AUDIT_LOG"
            echo "  Database: $AUDIT_DB"
            exit 1
            ;;
    esac
fi
