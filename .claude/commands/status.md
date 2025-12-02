---
description: Unified system status dashboard - all systems at a glance
allowed-tools: ["Bash", "Read", "mcp__general-server__get_disk_usage", "mcp__general-server__get_memory_info", "mcp__general-server__check_ebon_status", "mcp__general-server__skippy_health_check", "mcp__general-server__wp_cli_command", "mcp__general-server__skippy_circuit_breaker_status", "mcp__general-server__skippy_cache_stats"]
---

# Unified System Status Dashboard

Single command to check health of all systems. Replaces running 5+ separate status commands.

## Quick Status (Run All Checks)

Execute these checks in parallel for speed:

```bash
# === TIMESTAMP ===
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           SKIPPY UNIFIED STATUS DASHBOARD                    ║"
echo "║           $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
```

### 1. Local System Health
```bash
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 1. LOCAL SYSTEM                                             │"
echo "└─────────────────────────────────────────────────────────────┘"

# Disk usage (warn at 80%, critical at 90%)
DISK_PCT=$(df -h / | awk 'NR==2 {gsub(/%/,""); print $5}')
DISK_AVAIL=$(df -h / | awk 'NR==2 {print $4}')
if [ "$DISK_PCT" -ge 90 ]; then
  echo "  ❌ Disk: ${DISK_PCT}% used (${DISK_AVAIL} free) - CRITICAL"
elif [ "$DISK_PCT" -ge 80 ]; then
  echo "  ⚠️  Disk: ${DISK_PCT}% used (${DISK_AVAIL} free) - WARNING"
else
  echo "  ✅ Disk: ${DISK_PCT}% used (${DISK_AVAIL} free)"
fi

# Memory (warn at 80%, critical at 90%)
MEM_PCT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
MEM_AVAIL=$(free -h | awk '/Mem:/ {print $7}')
if [ "$MEM_PCT" -ge 90 ]; then
  echo "  ❌ Memory: ${MEM_PCT}% used (${MEM_AVAIL} available) - CRITICAL"
elif [ "$MEM_PCT" -ge 80 ]; then
  echo "  ⚠️  Memory: ${MEM_PCT}% used (${MEM_AVAIL} available) - WARNING"
else
  echo "  ✅ Memory: ${MEM_PCT}% used (${MEM_AVAIL} available)"
fi

# Load average
LOAD=$(uptime | awk -F'load average:' '{print $2}' | xargs)
CORES=$(nproc)
LOAD_1=$(echo "$LOAD" | cut -d',' -f1 | xargs)
LOAD_INT=$(echo "$LOAD_1" | cut -d'.' -f1)
if [ "$LOAD_INT" -ge "$CORES" ]; then
  echo "  ⚠️  Load: $LOAD (${CORES} cores) - HIGH"
else
  echo "  ✅ Load: $LOAD (${CORES} cores)"
fi

# Uptime
UPTIME=$(uptime -p)
echo "  ℹ️  Uptime: $UPTIME"
```

### 2. WordPress Sites
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 2. WORDPRESS SITES                                          │"
echo "└─────────────────────────────────────────────────────────────┘"

# Local site
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
LOCAL_URL="http://rundaverun-local-complete-022655.local"
PROD_URL="https://rundaverun.org"

# Check local WordPress
if wp --path="$WP_PATH" core is-installed 2>/dev/null; then
  WP_VER=$(wp --path="$WP_PATH" core version 2>/dev/null)
  ACTIVE_PLUGINS=$(wp --path="$WP_PATH" plugin list --status=active --format=count 2>/dev/null)
  echo "  ✅ Local: WordPress $WP_VER ($ACTIVE_PLUGINS plugins active)"
else
  echo "  ❌ Local: WordPress not responding"
fi

# Check local HTTP
LOCAL_HTTP=$(timeout 5 curl -sI "$LOCAL_URL" 2>/dev/null | head -1 | awk '{print $2}')
if [ "$LOCAL_HTTP" = "200" ]; then
  echo "  ✅ Local HTTP: $LOCAL_URL (200 OK)"
else
  echo "  ⚠️  Local HTTP: $LOCAL_URL (${LOCAL_HTTP:-timeout})"
fi

# Check production HTTP
PROD_HTTP=$(timeout 10 curl -sI "$PROD_URL" 2>/dev/null | head -1 | awk '{print $2}')
if [ "$PROD_HTTP" = "200" ]; then
  echo "  ✅ Production: $PROD_URL (200 OK)"
else
  echo "  ❌ Production: $PROD_URL (${PROD_HTTP:-timeout})"
fi
```

### 3. MCP Servers
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 3. MCP SERVERS                                              │"
echo "└─────────────────────────────────────────────────────────────┘"
```

Use MCP tools to check:
- `mcp__general-server__skippy_health_check` - Overall health
- `mcp__general-server__skippy_circuit_breaker_status` - Circuit breakers
- `mcp__general-server__skippy_cache_stats` - Cache health

Report:
- Number of tools available
- Any circuit breakers tripped
- Cache hit rate

### 4. Remote Server (Ebon)
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 4. REMOTE SERVER (EBON)                                     │"
echo "└─────────────────────────────────────────────────────────────┘"
```

Use `mcp__general-server__check_ebon_status` and report:
- Uptime
- Disk usage
- Memory usage
- Key services (Docker, Jellyfin)

### 5. Git Status
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 5. GIT STATUS                                               │"
echo "└─────────────────────────────────────────────────────────────┘"

cd /home/dave/skippy

# Current branch
BRANCH=$(git branch --show-current 2>/dev/null)
echo "  📌 Branch: $BRANCH"

# Uncommitted changes
CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
if [ "$CHANGES" -gt 0 ]; then
  echo "  ⚠️  Uncommitted: $CHANGES files"
else
  echo "  ✅ Working tree clean"
fi

# Ahead/behind
AHEAD=$(git rev-list --count origin/$BRANCH..$BRANCH 2>/dev/null || echo "?")
BEHIND=$(git rev-list --count $BRANCH..origin/$BRANCH 2>/dev/null || echo "?")
if [ "$AHEAD" != "0" ] || [ "$BEHIND" != "0" ]; then
  echo "  ℹ️  Ahead: $AHEAD, Behind: $BEHIND"
fi

# Last commit
LAST_COMMIT=$(git log -1 --format='%h %s (%cr)' 2>/dev/null)
echo "  📝 Last: $LAST_COMMIT"
```

### 6. Recent Work Sessions
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 6. RECENT WORK SESSIONS                                     │"
echo "└─────────────────────────────────────────────────────────────┘"

# Find most recent session directories
RECENT=$(find /home/dave/skippy/work -maxdepth 3 -type d -mmin -120 2>/dev/null | sort -r | head -3)
if [ -n "$RECENT" ]; then
  echo "$RECENT" | while read dir; do
    AGO=$(stat -c %Y "$dir" 2>/dev/null)
    NOW=$(date +%s)
    MINS=$(( (NOW - AGO) / 60 ))
    echo "  📂 ${dir##*/} (${MINS}m ago)"
  done
else
  echo "  ℹ️  No sessions in last 2 hours"
fi
```

### 7. Alerts & Warnings
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ 7. ALERTS & WARNINGS                                        │"
echo "└─────────────────────────────────────────────────────────────┘"

# Check for recent compactions
LAST_COMPACT=$(ls -t ~/.claude/compactions/ 2>/dev/null | head -1)
if [ -n "$LAST_COMPACT" ]; then
  COMPACT_TIME=$(stat -c %Y ~/.claude/compactions/$LAST_COMPACT 2>/dev/null)
  NOW=$(date +%s)
  HOURS=$(( (NOW - COMPACT_TIME) / 3600 ))
  if [ "$HOURS" -lt 2 ]; then
    echo "  ⚠️  Auto-compact ${HOURS}h ago - check ~/.claude/compactions/$LAST_COMPACT"
  fi
fi

# Check for error logs
if [ -f "/home/dave/skippy/rundaverun_local_site/app/public/wp-content/debug.log" ]; then
  ERRORS=$(tail -100 /home/dave/skippy/rundaverun_local_site/app/public/wp-content/debug.log 2>/dev/null | grep -c "Fatal\|Error" || echo 0)
  if [ "$ERRORS" -gt 0 ]; then
    echo "  ⚠️  WordPress debug.log: $ERRORS recent errors"
  fi
fi

# Check budget warnings
BUDGET_WARN=$(ls -t ~/.claude/budget_warnings/*.md 2>/dev/null | head -1)
if [ -n "$BUDGET_WARN" ]; then
  WARN_TIME=$(stat -c %Y "$BUDGET_WARN" 2>/dev/null)
  NOW=$(date +%s)
  MINS=$(( (NOW - WARN_TIME) / 60 ))
  if [ "$MINS" -lt 30 ]; then
    echo "  ⚠️  Context budget warning ${MINS}m ago"
  fi
fi

# If no alerts
echo "  ✅ No critical alerts" 2>/dev/null || true
```

### Summary Footer
```bash
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Quick Actions:"
echo "  • /deploy-verify  - Verify deployment + flush caches"
echo "  • /error-logs     - View aggregated error logs"
echo "  • /recover-session - Recover from compaction"
echo "══════════════════════════════════════════════════════════════"
```

## Output Format

The dashboard uses consistent visual indicators:

| Symbol | Meaning |
|--------|---------|
| ✅ | Healthy / OK |
| ⚠️ | Warning - needs attention |
| ❌ | Critical - action required |
| ℹ️ | Informational |
| 📌 | Current state |
| 📂 | Directory/file reference |
| 📝 | Text/content |

## Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk | 80% | 90% |
| Memory | 80% | 90% |
| Load | > cores | > 2x cores |
| HTTP | non-200 | timeout |
| Errors | > 0 | > 10 |

## Integration

This command aggregates data from:
- `/mcp-status` - MCP server health
- `/ebon-status` - Remote server health
- Local system tools (df, free, uptime)
- WordPress WP-CLI
- Git status
- Session directory scanning

## Usage

```bash
/status              # Full dashboard
/status --quick      # Just critical items (future)
/status --json       # Machine-readable output (future)
```
