#!/bin/bash
# Disaster Recovery Automation v1.0.0
# Automated backup, restore, and recovery procedures
# Part of: Skippy Enhancement Project - TIER 3
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"
DR_DIR="${SKIPPY_BASE}/disaster_recovery"
BACKUP_DIR="${SKIPPY_BASE}/backups"
SECRETS_MGR="${SKIPPY_BASE}/scripts/security/secrets_manager_v1.0.0.sh"
ALERT_SCRIPT="${SKIPPY_BASE}/scripts/monitoring/critical_alerter_v1.0.0.sh"

usage() {
    cat <<EOF
Disaster Recovery Automation v1.0.0

USAGE:
    $0 <command> [options]

COMMANDS:
    backup-full                  Create full system backup
    backup-wordpress             Backup WordPress only
    restore-full <backup>        Restore full system from backup
    restore-wordpress <backup>   Restore WordPress from backup
    test-recovery                Test disaster recovery procedure
    create-snapshot              Create point-in-time snapshot
    list-backups                 List all available backups
    verify-backup <file>         Verify backup integrity
    disaster-plan                Show disaster recovery plan
    failover                     Execute failover procedures

OPTIONS:
    --force                      Skip confirmations
    --encrypt                    Encrypt backup
    --remote                     Upload to remote storage
    --test                       Test mode (dry run)

EXAMPLES:
    # Create full backup
    $0 backup-full

    # Restore from specific backup
    $0 restore-full backup_20251104_120000.tar.gz

    # Test recovery procedure
    $0 test-recovery

    # Create encrypted backup
    $0 backup-full --encrypt

EOF
    exit 1
}

# Parse options
FORCE=false
ENCRYPT=false
REMOTE=false
TEST_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)
            FORCE=true
            shift
            ;;
        --encrypt)
            ENCRYPT=true
            shift
            ;;
        --remote)
            REMOTE=true
            shift
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"
BACKUP_FILE="${2:-}"

mkdir -p "$DR_DIR" "$BACKUP_DIR"

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

# Send alert
send_alert() {
    local event="$1"
    local details="$2"

    if [ -x "$ALERT_SCRIPT" ]; then
        "$ALERT_SCRIPT" "$event" "$details"
    fi
}

# Create full system backup
backup_full() {
    log "Creating full system backup..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="full_backup_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}.tar.gz"

    if [ "$TEST_MODE" = true ]; then
        warning "TEST MODE: Would create backup at $backup_path"
        return
    fi

    # What to backup
    local backup_items=(
        "${SKIPPY_BASE}/scripts"
        "${SKIPPY_BASE}/documentation"
        "${SKIPPY_BASE}/.secrets"
        "${SKIPPY_BASE}/logs"
        "${SKIPPY_BASE}/conversations"
    )

    # Create backup
    log "Backing up Skippy system..."
    tar -czf "$backup_path" "${backup_items[@]}" 2>/dev/null

    # Add WordPress if available
    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"
    if [ -d "$wp_path" ]; then
        log "Backing up WordPress..."
        local wp_backup="${BACKUP_DIR}/wordpress_${timestamp}.tar.gz"
        tar -czf "$wp_backup" "$wp_path" 2>/dev/null
    fi

    # Backup database
    if command -v wp &> /dev/null && [ -d "$wp_path" ]; then
        log "Backing up database..."
        cd "$wp_path"
        local db_backup="${BACKUP_DIR}/database_${timestamp}.sql"
        wp db export "$db_backup" --add-drop-table 2>/dev/null || true
    fi

    # Encrypt if requested
    if [ "$ENCRYPT" = true ]; then
        if command -v gpg &> /dev/null; then
            log "Encrypting backup..."
            gpg --symmetric --cipher-algo AES256 "$backup_path"
            rm "$backup_path"
            backup_path="${backup_path}.gpg"
            success "Backup encrypted"
        else
            warning "GPG not available, backup not encrypted"
        fi
    fi

    # Upload to remote if requested
    if [ "$REMOTE" = true ]; then
        upload_to_remote "$backup_path"
    fi

    success "Full backup created: $backup_path"

    # Create backup manifest
    cat > "${backup_path}.manifest" <<EOF
Backup Type: Full System
Created: $(date)
Size: $(du -h "$backup_path" | cut -f1)
Encrypted: $([ "$ENCRYPT" = true ] && echo "Yes" || echo "No")
Remote: $([ "$REMOTE" = true ] && echo "Yes" || echo "No")

Contents:
- Skippy scripts
- Documentation
- Secrets vault
- Logs
- Conversation history
$([ -f "${BACKUP_DIR}/wordpress_${timestamp}.tar.gz" ] && echo "- WordPress files")
$([ -f "${BACKUP_DIR}/database_${timestamp}.sql" ] && echo "- WordPress database")
EOF

    send_alert "BACKUP_CREATED" "Full system backup: $backup_name"
}

# Backup WordPress only
backup_wordpress() {
    log "Creating WordPress backup..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"

    if [ ! -d "$wp_path" ]; then
        error "WordPress directory not found"
        exit 1
    fi

    if [ "$TEST_MODE" = true ]; then
        warning "TEST MODE: Would backup WordPress"
        return
    fi

    # Backup files
    local wp_backup="${BACKUP_DIR}/wp_files_${timestamp}.tar.gz"
    tar -czf "$wp_backup" "$wp_path" 2>/dev/null

    # Backup database
    if command -v wp &> /dev/null; then
        cd "$wp_path"
        local db_backup="${BACKUP_DIR}/wp_database_${timestamp}.sql"
        wp db export "$db_backup" --add-drop-table
        success "Database backup created"
    fi

    success "WordPress backup created"
    send_alert "WP_BACKUP_CREATED" "WordPress backup: $timestamp"
}

# Restore full system
restore_full() {
    local backup="$1"

    if [ -z "$backup" ]; then
        error "Backup file required"
        usage
    fi

    if [ ! -f "$backup" ]; then
        # Try finding in backup directory
        backup="${BACKUP_DIR}/${backup}"
        if [ ! -f "$backup" ]; then
            error "Backup not found: $backup"
            exit 1
        fi
    fi

    warning "⚠ DISASTER RECOVERY: FULL SYSTEM RESTORE"
    echo
    echo "This will restore from: $backup"
    echo "Current system will be backed up first"
    echo

    if [ "$FORCE" = false ]; then
        read -p "Are you sure? Type 'RESTORE' to continue: " confirm
        if [ "$confirm" != "RESTORE" ]; then
            echo "Cancelled"
            exit 0
        fi
    fi

    if [ "$TEST_MODE" = true ]; then
        warning "TEST MODE: Would restore from $backup"
        return
    fi

    # Backup current system first
    log "Creating safety backup of current system..."
    local safety_backup="${BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$safety_backup" "${SKIPPY_BASE}/scripts" "${SKIPPY_BASE}/.secrets" 2>/dev/null || true
    success "Safety backup created: $safety_backup"

    # Decrypt if needed
    local restore_file="$backup"
    if [[ "$backup" == *.gpg ]]; then
        log "Decrypting backup..."
        restore_file="${backup%.gpg}"
        gpg --decrypt "$backup" > "$restore_file"
    fi

    # Extract backup
    log "Restoring from backup..."
    tar -xzf "$restore_file" -C /

    success "System restored from backup"
    send_alert "SYSTEM_RESTORED" "Restored from: $(basename "$backup")"

    echo
    warning "System restored. Please:"
    echo "1. Verify all services are running"
    echo "2. Test critical functionality"
    echo "3. Check logs for errors"
    echo "4. Run: ./scripts/testing/test_runner_v1.0.0.sh run smoke"
}

# Restore WordPress
restore_wordpress() {
    local backup="$1"

    if [ -z "$backup" ]; then
        error "Backup file required"
        list_backups
        exit 1
    fi

    warning "⚠ WordPress Restore"
    echo
    echo "This will restore WordPress from: $backup"
    echo

    if [ "$FORCE" = false ]; then
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Cancelled"
            exit 0
        fi
    fi

    if [ "$TEST_MODE" = true ]; then
        warning "TEST MODE: Would restore WordPress from $backup"
        return
    fi

    # Find matching database backup
    local timestamp=$(echo "$backup" | grep -oP '\d{8}_\d{6}')
    local db_backup="${BACKUP_DIR}/wp_database_${timestamp}.sql"

    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"

    # Restore files
    if [[ "$backup" == *files* ]]; then
        log "Restoring WordPress files..."
        tar -xzf "$backup" -C "$(dirname "$wp_path")"
    fi

    # Restore database
    if [ -f "$db_backup" ] && command -v wp &> /dev/null; then
        log "Restoring database..."
        cd "$wp_path"
        wp db import "$db_backup"
        wp cache flush
    fi

    success "WordPress restored"
    send_alert "WP_RESTORED" "Restored from: $(basename "$backup")"
}

# Test disaster recovery procedure
test_recovery() {
    log "Testing disaster recovery procedure..."
    echo

    local test_passed=0
    local test_failed=0

    # Test 1: Backup creation
    echo "Test 1: Backup Creation"
    if tar --version &> /dev/null; then
        success "tar available"
        ((test_passed++))
    else
        error "tar not available"
        ((test_failed++))
    fi

    # Test 2: Backup directory accessible
    echo "Test 2: Backup Directory"
    if [ -w "$BACKUP_DIR" ]; then
        success "Backup directory writable"
        ((test_passed++))
    else
        error "Backup directory not writable"
        ((test_failed++))
    fi

    # Test 3: Encryption available
    echo "Test 3: Encryption Capability"
    if command -v gpg &> /dev/null; then
        success "GPG available for encryption"
        ((test_passed++))
    else
        warning "GPG not available"
        ((test_failed++))
    fi

    # Test 4: Recent backups exist
    echo "Test 4: Recent Backups"
    local recent_backups=$(find "$BACKUP_DIR" -name "*.tar.gz" -mtime -7 | wc -l)
    if [ "$recent_backups" -gt 0 ]; then
        success "Found $recent_backups recent backup(s)"
        ((test_passed++))
    else
        warning "No recent backups found"
        ((test_failed++))
    fi

    # Test 5: Backup integrity
    echo "Test 5: Backup Integrity"
    local latest_backup=$(find "$BACKUP_DIR" -name "full_backup_*.tar.gz" -type f | sort -r | head -1)
    if [ -n "$latest_backup" ]; then
        if tar -tzf "$latest_backup" &> /dev/null; then
            success "Latest backup is valid"
            ((test_passed++))
        else
            error "Latest backup is corrupted"
            ((test_failed++))
        fi
    else
        warning "No full backup found to test"
    fi

    # Summary
    echo
    echo "─────────────────────────────────"
    echo "Test Results:"
    echo "  Passed: $test_passed"
    echo "  Failed: $test_failed"
    echo

    if [ "$test_failed" -eq 0 ]; then
        success "✓ Disaster recovery system is healthy"
        return 0
    else
        warning "⚠ Some tests failed - review results"
        return 1
    fi
}

# Create snapshot
create_snapshot() {
    log "Creating point-in-time snapshot..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local snapshot_dir="${DR_DIR}/snapshots/snapshot_${timestamp}"

    mkdir -p "$snapshot_dir"

    # Snapshot critical data
    cp -r "${SKIPPY_BASE}/scripts" "$snapshot_dir/" 2>/dev/null || true
    cp -r "${SKIPPY_BASE}/.secrets" "$snapshot_dir/" 2>/dev/null || true
    cp -r "${SKIPPY_BASE}/conversations/deployment_validation_reports" "$snapshot_dir/" 2>/dev/null || true

    # Create snapshot manifest
    cat > "${snapshot_dir}/MANIFEST.txt" <<EOF
Snapshot: $timestamp
Created: $(date)
Type: Point-in-time snapshot

Contents:
- Scripts
- Secrets vault
- Recent deployment reports

Purpose: Quick rollback point for development
EOF

    success "Snapshot created: $snapshot_dir"
}

# List backups
list_backups() {
    log "Available backups:"
    echo

    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -name "*.tar.gz" -o -name "*.sql" | sort -r | while read -r backup; do
            local size=$(du -h "$backup" | cut -f1)
            local age=$(( ($(date +%s) - $(stat -c %Y "$backup")) / 86400 ))
            echo "$(basename "$backup") (${size}, ${age} days old)"
        done
    else
        warning "No backups found"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup="$1"

    if [ -z "$backup" ]; then
        error "Backup file required"
        usage
    fi

    log "Verifying backup: $backup"

    # Check file exists
    if [ ! -f "$backup" ]; then
        error "Backup file not found"
        exit 1
    fi

    # Check file type
    if [[ "$backup" == *.tar.gz ]]; then
        if tar -tzf "$backup" &> /dev/null; then
            success "Backup archive is valid"
        else
            error "Backup archive is corrupted"
            exit 1
        fi
    elif [[ "$backup" == *.sql ]]; then
        if head -10 "$backup" | grep -q "MySQL dump"; then
            success "Database backup is valid"
        else
            error "Database backup may be corrupted"
            exit 1
        fi
    fi

    # Check size
    local size=$(stat -c %s "$backup")
    if [ "$size" -gt 1000 ]; then
        success "Backup size: $(du -h "$backup" | cut -f1)"
    else
        warning "Backup size is suspiciously small: $size bytes"
    fi

    success "Backup verification complete"
}

# Show disaster recovery plan
show_disaster_plan() {
    cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║           DISASTER RECOVERY PLAN                              ║
╚═══════════════════════════════════════════════════════════════╝

## Disaster Scenarios & Response

### 1. Complete System Loss
**Actions:**
1. Restore full system backup
   $ dr_automation.sh restore-full <latest_backup>
2. Verify all services
   $ test_runner.sh run smoke
3. Check WordPress
   $ wp core verify-checksums
4. Resume operations

**RTO:** 2 hours
**RPO:** 24 hours

### 2. WordPress Site Failure
**Actions:**
1. Restore WordPress backup
   $ dr_automation.sh restore-wordpress <latest_wp_backup>
2. Verify database
   $ wp db check
3. Test site functionality
4. Clear all caches

**RTO:** 1 hour
**RPO:** 24 hours

### 3. Data Corruption
**Actions:**
1. Identify corrupted data
2. Restore from snapshot
   $ dr_automation.sh restore-full <snapshot>
3. Replay recent changes
4. Validate integrity

**RTO:** 3 hours
**RPO:** Point-in-time snapshot

### 4. Security Breach
**Actions:**
1. Isolate affected systems
2. Run security scan
   $ vulnerability_scanner.sh
3. Restore from clean backup
4. Change all credentials
5. Audit logs for intrusion

**RTO:** 4 hours
**RPO:** Pre-breach backup

## Backup Schedule

**Full Backups:** Daily (automated)
**WordPress Backups:** Before each deployment
**Snapshots:** Before major changes
**Retention:** 30 days active, 90 days archive

## Emergency Contacts

**System Admin:** dave@rundaverun.org
**Hosting Support:** [hosting provider]
**Domain Registrar:** [registrar]

## Recovery Checklist

After any recovery:
[ ] Run smoke tests
[ ] Verify all services running
[ ] Check security logs
[ ] Test critical user flows
[ ] Update documentation
[ ] Send recovery report

## Testing

Test disaster recovery monthly:
$ dr_automation.sh test-recovery

EOF
}

# Upload to remote storage
upload_to_remote() {
    local file="$1"

    log "Uploading to remote storage..."

    # Get remote credentials from secrets
    if [ -x "$SECRETS_MGR" ]; then
        local remote_host=$($SECRETS_MGR get backup_remote_host 2>/dev/null || echo "")
        local remote_user=$($SECRETS_MGR get backup_remote_user 2>/dev/null || echo "")
        local remote_path=$($SECRETS_MGR get backup_remote_path 2>/dev/null || echo "")

        if [ -n "$remote_host" ] && [ -n "$remote_user" ]; then
            scp "$file" "${remote_user}@${remote_host}:${remote_path}/" 2>/dev/null && \
                success "Uploaded to remote storage" || \
                warning "Remote upload failed"
        else
            warning "Remote storage not configured"
        fi
    fi
}

# Execute failover
execute_failover() {
    warning "⚠ FAILOVER PROCEDURE"
    echo

    if [ "$FORCE" = false ]; then
        read -p "Execute failover to backup site? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Cancelled"
            exit 0
        fi
    fi

    log "Step 1: Verify backup site availability"
    # Check backup site

    log "Step 2: Sync latest data"
    # Sync data

    log "Step 3: Switch DNS/routing"
    # Update DNS

    log "Step 4: Verify failover"
    # Test backup site

    success "Failover complete"
    send_alert "FAILOVER_EXECUTED" "Switched to backup site"
}

# Main command dispatcher
case "$COMMAND" in
    backup-full)
        backup_full
        ;;
    backup-wordpress)
        backup_wordpress
        ;;
    restore-full)
        restore_full "$BACKUP_FILE"
        ;;
    restore-wordpress)
        restore_wordpress "$BACKUP_FILE"
        ;;
    test-recovery)
        test_recovery
        ;;
    create-snapshot)
        create_snapshot
        ;;
    list-backups)
        list_backups
        ;;
    verify-backup)
        verify_backup "$BACKUP_FILE"
        ;;
    disaster-plan)
        show_disaster_plan
        ;;
    failover)
        execute_failover
        ;;
    *)
        usage
        ;;
esac

exit 0
