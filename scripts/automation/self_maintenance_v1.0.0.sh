#!/bin/bash
# Self-Maintenance System v1.0.0
# Automatic system health monitoring and self-healing
# Part of: Skippy Enhancement Project - TIER 4
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
MAINTENANCE_LOG="${SKIPPY_BASE}/logs/maintenance/self_maintenance.log"
ALERT_SCRIPT="${SKIPPY_BASE}/scripts/monitoring/critical_alerter_v1.0.0.sh"

usage() {
    cat <<EOF
Self-Maintenance System v1.0.0

USAGE:
    $0 <command> [options]

COMMANDS:
    run                          Run full maintenance cycle
    check                        Check system health
    auto-heal                    Attempt automatic healing
    monitor                      Continuous monitoring mode
    fix <issue>                  Fix specific issue
    status                       Show maintenance status
    schedule                     Setup scheduled maintenance

ISSUES IT CAN FIX:
    disk-space                   Clean up disk space
    permissions                  Fix file permissions
    logs                         Rotate/clean old logs
    backups                      Verify and fix backup issues
    dependencies                 Check/install missing dependencies
    config                       Fix configuration issues

OPTIONS:
    --auto                       Automatic mode (no prompts)
    --dry-run                    Show what would be done
    --interval <seconds>         Monitoring interval (default: 300)

EXAMPLES:
    # Run full maintenance
    $0 run

    # Continuous monitoring
    $0 monitor

    # Auto-heal specific issue
    $0 fix disk-space --auto

    # Setup cron job
    $0 schedule

EOF
    exit 1
}

# Parse options
AUTO_MODE=false
DRY_RUN=false
MONITOR_INTERVAL=300

while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"
ISSUE="${2:-}"

mkdir -p "$(dirname "$MAINTENANCE_LOG")"

log_maintenance() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" | tee -a "$MAINTENANCE_LOG"
}

log() {
    echo -e "${BLUE}$1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
    log_maintenance "SUCCESS: $1"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    log_maintenance "WARNING: $1"
}

error() {
    echo -e "${RED}✗ $1${NC}"
    log_maintenance "ERROR: $1"
}

# Send alert
send_alert() {
    local event="$1"
    local details="$2"

    if [ -x "$ALERT_SCRIPT" ]; then
        "$ALERT_SCRIPT" "$event" "$details" 2>/dev/null || true
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df -h "$SKIPPY_BASE" | awk 'NR==2 {print $5}' | tr -d '%')

    if [ "$usage" -gt 90 ]; then
        error "Disk space critical: ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        warning "Disk space high: ${usage}%"
        return 2
    else
        success "Disk space OK: ${usage}%"
        return 0
    fi
}

# Fix disk space
fix_disk_space() {
    log "Fixing disk space issues..."

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would clean disk space"
        return
    fi

    # Clean old logs
    log "  Cleaning old logs..."
    find "${SKIPPY_BASE}/logs" -name "*.log" -mtime +60 -delete 2>/dev/null || true

    # Rotate aggregated logs
    log "  Rotating aggregated logs..."
    if [ -x "${SKIPPY_BASE}/scripts/monitoring/log_aggregator_v1.0.0.sh" ]; then
        "${SKIPPY_BASE}/scripts/monitoring/log_aggregator_v1.0.0.sh" rotate 2>/dev/null || true
    fi

    # Clean old backups
    log "  Cleaning old backups (keep 30 days)..."
    find "${SKIPPY_BASE}/backups" -name "*.sql" -mtime +30 -delete 2>/dev/null || true
    find "${SKIPPY_BASE}/backups" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true

    # Clean work files
    log "  Cleaning old work files..."
    if [ -x "${SKIPPY_BASE}/scripts/cleanup_work_files.sh" ]; then
        "${SKIPPY_BASE}/scripts/cleanup_work_files.sh" 2>/dev/null || true
    fi

    # Clean old reports
    log "  Cleaning old reports (keep 60 days)..."
    find "${SKIPPY_BASE}/conversations" -name "*.md" -mtime +60 -delete 2>/dev/null || true

    success "Disk space cleanup complete"
}

# Check file permissions
check_permissions() {
    log "Checking file permissions..."

    local issues=0

    # Check secrets directory
    if [ -d "${SKIPPY_BASE}/.secrets" ]; then
        local perms=$(stat -c %a "${SKIPPY_BASE}/.secrets" 2>/dev/null || echo "000")
        if [ "$perms" != "700" ]; then
            warning "Secrets directory permissions: $perms (should be 700)"
            ((issues++))
        fi
    fi

    # Check for world-writable files
    local writable=$(find "${SKIPPY_BASE}/scripts" -type f -perm -002 2>/dev/null | wc -l)
    if [ "$writable" -gt 0 ]; then
        warning "Found $writable world-writable scripts"
        ((issues++))
    fi

    # Check script executability
    local non_executable=$(find "${SKIPPY_BASE}/scripts" -name "*_v[0-9]*.sh" -type f ! -executable 2>/dev/null | wc -l)
    if [ "$non_executable" -gt 0 ]; then
        warning "Found $non_executable non-executable scripts"
        ((issues++))
    fi

    if [ $issues -eq 0 ]; then
        success "File permissions OK"
        return 0
    else
        warning "Found $issues permission issues"
        return 1
    fi
}

# Fix file permissions
fix_permissions() {
    log "Fixing file permissions..."

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would fix permissions"
        return
    fi

    # Fix secrets directory
    if [ -d "${SKIPPY_BASE}/.secrets" ]; then
        chmod 700 "${SKIPPY_BASE}/.secrets"
        log "  Fixed secrets directory permissions"
    fi

    # Fix world-writable scripts
    find "${SKIPPY_BASE}/scripts" -type f -perm -002 -exec chmod 644 {} \; 2>/dev/null || true
    log "  Removed world-write permissions"

    # Make scripts executable
    find "${SKIPPY_BASE}/scripts" -name "*_v[0-9]*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
    log "  Made scripts executable"

    success "Permissions fixed"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."

    local missing=0

    # Essential commands
    local deps=("bash" "jq" "curl" "grep" "sed" "awk")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            warning "Missing: $dep"
            ((missing++))
        fi
    done

    if [ $missing -eq 0 ]; then
        success "All dependencies present"
        return 0
    else
        warning "Missing $missing dependencies"
        return 1
    fi
}

# Check backups
check_backups() {
    log "Checking backups..."

    local latest_backup=$(find "${SKIPPY_BASE}/backups" -name "*.tar.gz" -o -name "*.sql" | sort -r | head -1)

    if [ -z "$latest_backup" ]; then
        warning "No backups found"
        return 1
    fi

    local backup_age=$(( ($(date +%s) - $(stat -c %Y "$latest_backup")) / 3600 ))

    if [ "$backup_age" -gt 48 ]; then
        warning "Latest backup is $backup_age hours old"
        return 1
    else
        success "Latest backup: $backup_age hours old"
        return 0
    fi
}

# Fix backup issues
fix_backups() {
    log "Fixing backup issues..."

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would create backup"
        return
    fi

    # Create new backup
    if [ -x "${SKIPPY_BASE}/scripts/disaster_recovery/dr_automation_v1.0.0.sh" ]; then
        log "  Creating new backup..."
        "${SKIPPY_BASE}/scripts/disaster_recovery/dr_automation_v1.0.0.sh" backup-full 2>/dev/null || {
            warning "Backup creation failed"
            return 1
        }
        success "Backup created"
    else
        warning "Backup script not found"
        return 1
    fi
}

# Check configuration
check_configuration() {
    log "Checking configuration..."

    local issues=0

    # Check directory structure
    local required_dirs=(
        "${SKIPPY_BASE}/scripts"
        "${SKIPPY_BASE}/logs"
        "${SKIPPY_BASE}/backups"
        "${SKIPPY_BASE}/conversations"
    )

    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            warning "Missing directory: $dir"
            ((issues++))
        fi
    done

    if [ $issues -eq 0 ]; then
        success "Configuration OK"
        return 0
    else
        warning "Found $issues configuration issues"
        return 1
    fi
}

# Fix configuration
fix_configuration() {
    log "Fixing configuration..."

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would fix configuration"
        return
    fi

    # Create missing directories
    local dirs=(
        "${SKIPPY_BASE}/scripts"
        "${SKIPPY_BASE}/logs/security"
        "${SKIPPY_BASE}/logs/alerts"
        "${SKIPPY_BASE}/logs/maintenance"
        "${SKIPPY_BASE}/backups"
        "${SKIPPY_BASE}/conversations"
        "${SKIPPY_BASE}/work/active"
        "${SKIPPY_BASE}/work/archive"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "  Created: $dir"
        fi
    done

    success "Configuration fixed"
}

# Full health check
health_check() {
    log "Running health check..."
    echo

    local total_checks=0
    local passed_checks=0
    local failed_checks=0

    # Run all checks
    ((total_checks++)) && check_disk_space && ((passed_checks++)) || ((failed_checks++))
    echo

    ((total_checks++)) && check_permissions && ((passed_checks++)) || ((failed_checks++))
    echo

    ((total_checks++)) && check_dependencies && ((passed_checks++)) || ((failed_checks++))
    echo

    ((total_checks++)) && check_backups && ((passed_checks++)) || ((failed_checks++))
    echo

    ((total_checks++)) && check_configuration && ((passed_checks++)) || ((failed_checks++))
    echo

    # Summary
    echo "═══════════════════════════════════════"
    log "Health Check Summary:"
    echo "  Total checks: $total_checks"
    echo "  Passed: $passed_checks"
    echo "  Failed: $failed_checks"
    echo

    local health_percent=$(( passed_checks * 100 / total_checks ))
    log "System Health: ${health_percent}%"

    if [ $failed_checks -eq 0 ]; then
        success "System is healthy"
        return 0
    else
        warning "System has $failed_checks issues"
        return 1
    fi
}

# Auto-heal all issues
auto_heal() {
    log "Starting auto-heal..."
    echo

    # Run health check first
    health_check > /dev/null 2>&1

    # Fix issues
    if ! check_disk_space > /dev/null 2>&1; then
        log "Healing: Disk space"
        fix_disk_space
        echo
    fi

    if ! check_permissions > /dev/null 2>&1; then
        log "Healing: Permissions"
        fix_permissions
        echo
    fi

    if ! check_backups > /dev/null 2>&1; then
        log "Healing: Backups"
        fix_backups
        echo
    fi

    if ! check_configuration > /dev/null 2>&1; then
        log "Healing: Configuration"
        fix_configuration
        echo
    fi

    success "Auto-heal complete"

    # Run health check again
    echo
    health_check
}

# Run full maintenance
run_maintenance() {
    log "Starting maintenance cycle..."
    log_maintenance "=== Maintenance Cycle Started ==="
    echo

    # Health check
    log "Step 1: Health Check"
    health_check
    echo

    # Auto-heal if issues found
    if [ $? -ne 0 ]; then
        log "Step 2: Auto-Heal"
        auto_heal
        echo
    fi

    # Optimize performance
    log "Step 3: Performance Optimization"
    if [ -x "${SKIPPY_BASE}/scripts/optimization/performance_optimizer_v1.0.0.sh" ]; then
        "${SKIPPY_BASE}/scripts/optimization/performance_optimizer_v1.0.0.sh" optimize-scripts 2>/dev/null || true
    fi
    echo

    # Rotate logs
    log "Step 4: Log Rotation"
    if [ -x "${SKIPPY_BASE}/scripts/monitoring/log_aggregator_v1.0.0.sh" ]; then
        "${SKIPPY_BASE}/scripts/monitoring/log_aggregator_v1.0.0.sh" rotate 2>/dev/null || true
    fi
    echo

    log_maintenance "=== Maintenance Cycle Complete ==="
    success "Maintenance cycle complete"
}

# Continuous monitoring
monitor_mode() {
    log "Starting continuous monitoring (interval: ${MONITOR_INTERVAL}s)"
    log "Press Ctrl+C to stop"
    echo

    while true; do
        log "=== Monitoring Check: $(date) ==="

        # Quick health check
        health_check > /tmp/health_check_$$.log 2>&1

        if [ $? -ne 0 ]; then
            warning "Health issues detected"

            if [ "$AUTO_MODE" = true ]; then
                log "Auto-healing..."
                auto_heal > /tmp/auto_heal_$$.log 2>&1
                send_alert "AUTO_HEAL" "System auto-healed issues"
            else
                cat /tmp/health_check_$$.log
                warning "Run with --auto for automatic healing"
            fi
        else
            success "System healthy"
        fi

        echo
        log "Next check in ${MONITOR_INTERVAL}s..."
        sleep "$MONITOR_INTERVAL"
        echo
    done
}

# Fix specific issue
fix_issue() {
    local issue="$1"

    case "$issue" in
        disk-space)
            fix_disk_space
            ;;
        permissions)
            fix_permissions
            ;;
        logs)
            fix_disk_space
            ;;
        backups)
            fix_backups
            ;;
        config)
            fix_configuration
            ;;
        *)
            error "Unknown issue: $issue"
            usage
            ;;
    esac
}

# Show maintenance status
show_status() {
    log "Maintenance Status"
    echo

    # Last maintenance
    if [ -f "$MAINTENANCE_LOG" ]; then
        local last_run=$(grep "Maintenance Cycle Complete" "$MAINTENANCE_LOG" | tail -1 | awk '{print $1, $2}')
        log "Last maintenance: $last_run"
    else
        warning "No maintenance history"
    fi

    # Current health
    echo
    health_check
}

# Setup scheduled maintenance
setup_schedule() {
    log "Setting up scheduled maintenance..."

    local cron_entry="0 3 * * 0 ${SKIPPY_BASE}/scripts/automation/self_maintenance_v1.0.0.sh run --auto >> ${MAINTENANCE_LOG} 2>&1"

    # Check if already scheduled
    if crontab -l 2>/dev/null | grep -q "self_maintenance"; then
        success "Scheduled maintenance already configured"
        return
    fi

    if [ "$AUTO_MODE" = false ]; then
        echo
        echo "This will add a cron job to run maintenance:"
        echo "  - Every Sunday at 3:00 AM"
        echo "  - Automatic mode (no prompts)"
        echo
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Cancelled"
            return
        fi
    fi

    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -

    success "Scheduled maintenance configured"
    log "  Schedule: Every Sunday at 3:00 AM"
}

# Main command dispatcher
case "$COMMAND" in
    run)
        run_maintenance
        ;;
    check)
        health_check
        ;;
    auto-heal)
        auto_heal
        ;;
    monitor)
        monitor_mode
        ;;
    fix)
        fix_issue "$ISSUE"
        ;;
    status)
        show_status
        ;;
    schedule)
        setup_schedule
        ;;
    *)
        usage
        ;;
esac

exit 0
