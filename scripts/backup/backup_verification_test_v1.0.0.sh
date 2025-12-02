#!/bin/bash
# Backup Verification Test v1.0.0
# Automatically tests backup integrity and restorability
# Part of: Skippy Security Enhancement Project - Phase 1
# Author: Claude (Skippy Enhancement Project)
# Created: 2025-11-04

set -euo pipefail

# Configuration
SKIP PY_BASE="/home/dave/skippy"
BACKUP_DIR="/home/dave/backups"  # Adjust to your backup location
GDRIVE_BACKUP="/home/dave/Google Drive/Backups"  # Adjust to actual path
TEST_DIR="/tmp/backup_verification_test_$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${SKIPPY_BASE}/logs/backup_verification"
REPORT_DIR="${SKIPPY_BASE}/conversations/backup_reports"
ERROR_LOG="${SKIPPY_BASE}/conversations/error_logs/$(date +%Y-%m)/$(date +%Y%m%d_%H%M%S)_backup_verification.log"
TEST_REPORT="${REPORT_DIR}/backup_verification_$(date +%Y%m%d_%H%M%S).md"

# Email notification settings (configure for your system)
NOTIFY_EMAIL="${NOTIFY_EMAIL:-dave@rundaverun.org}"
SEND_EMAIL=false  # Set to true to enable email notifications

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create directories
mkdir -p "$LOG_DIR" "$REPORT_DIR" "$(dirname "$ERROR_LOG")" "$TEST_DIR"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_DIR}/verification.log"
}

log_error() {
    echo "[ERROR] $1" | tee -a "$ERROR_LOG"
}

# Cleanup on exit
cleanup() {
    log "Cleaning up test directory: $TEST_DIR"
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Start report
cat > "$TEST_REPORT" <<EOF
# Backup Verification Test Report

**Test Date:** $(date)
**Test Version:** 1.0.0
**System:** $(hostname)
**Test Directory:** $TEST_DIR

---

## Summary

EOF

echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Backup Verification Test v1.0.0         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

log "Starting backup verification test"

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

#═══════════════════════════════════════════════════════════════
# TEST 1: Find Latest Backups
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[1/7] Locating latest backups...${NC}"

# Find most recent full backup
LATEST_BACKUP=""
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.tar.gz" -o -name "*.zip" | sort -r | head -1)
fi

if [ -z "$LATEST_BACKUP" ] && [ -d "$GDRIVE_BACKUP" ]; then
    LATEST_BACKUP=$(find "$GDRIVE_BACKUP" -name "*.tar.gz" -o -name "*.zip" | sort -r | head -1)
fi

if [ -n "$LATEST_BACKUP" ]; then
    echo -e "${GREEN}✓ Found backup: $(basename "$LATEST_BACKUP")${NC}"
    log "Using backup: $LATEST_BACKUP"

    BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
    BACKUP_DATE=$(stat -c %y "$LATEST_BACKUP" | cut -d' ' -f1)

    cat >> "$TEST_REPORT" <<EOF
### Latest Backup Located

- **File:** $(basename "$LATEST_BACKUP")
- **Path:** $LATEST_BACKUP
- **Size:** $BACKUP_SIZE
- **Date:** $BACKUP_DATE
- **Age:** $(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 86400 )) days old

EOF
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ No backup files found${NC}"
    log_error "No backup files found in $BACKUP_DIR or $GDRIVE_BACKUP"

    cat >> "$TEST_REPORT" <<EOF
### Latest Backup: NOT FOUND

**CRITICAL:** No backup files found in configured locations.

**Checked:**
- $BACKUP_DIR
- $GDRIVE_BACKUP

EOF
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

#═══════════════════════════════════════════════════════════════
# TEST 2: Backup File Integrity
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[2/7] Testing backup file integrity...${NC}"

if [ -n "$LATEST_BACKUP" ]; then
    log "Checking file integrity"

    # Test if file is readable
    if [ -r "$LATEST_BACKUP" ]; then
        echo -e "${GREEN}✓ Backup file is readable${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Check file type and test extraction
        FILE_TYPE=$(file "$LATEST_BACKUP" | cut -d: -f2)

        if [[ "$LATEST_BACKUP" == *.tar.gz ]]; then
            if tar -tzf "$LATEST_BACKUP" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ tar.gz archive is valid${NC}"
                TESTS_PASSED=$((TESTS_PASSED + 1))

                cat >> "$TEST_REPORT" <<EOF
### File Integrity: PASS

- **File Type:** $FILE_TYPE
- **Archive Test:** Valid tar.gz archive
- **Readable:** Yes

EOF
            else
                echo -e "${RED}✗ tar.gz archive is corrupted${NC}"
                log_error "Backup archive is corrupted: $LATEST_BACKUP"
                TESTS_FAILED=$((TESTS_FAILED + 1))

                cat >> "$TEST_REPORT" <<EOF
### File Integrity: FAIL

**CRITICAL:** Backup archive is corrupted and cannot be extracted.

EOF
            fi
        elif [[ "$LATEST_BACKUP" == *.zip ]]; then
            if unzip -t "$LATEST_BACKUP" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ zip archive is valid${NC}"
                TESTS_PASSED=$((TESTS_PASSED + 1))

                cat >> "$TEST_REPORT" <<EOF
### File Integrity: PASS

- **File Type:** $FILE_TYPE
- **Archive Test:** Valid zip archive
- **Readable:** Yes

EOF
            else
                echo -e "${RED}✗ zip archive is corrupted${NC}"
                log_error "Backup archive is corrupted: $LATEST_BACKUP"
                TESTS_FAILED=$((TESTS_FAILED + 1))

                cat >> "$TEST_REPORT" <<EOF
### File Integrity: FAIL

**CRITICAL:** Backup archive is corrupted and cannot be extracted.

EOF
            fi
        fi
    else
        echo -e "${RED}✗ Backup file is not readable${NC}"
        log_error "Cannot read backup file: $LATEST_BACKUP"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no backup found)${NC}"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
fi

#═══════════════════════════════════════════════════════════════
# TEST 3: Extract Sample Files
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[3/7] Testing partial extraction...${NC}"

if [ -n "$LATEST_BACKUP" ]; then
    log "Attempting partial extraction"

    mkdir -p "$TEST_DIR/extract_test"

    if [[ "$LATEST_BACKUP" == *.tar.gz ]]; then
        # Extract first 10 files only (faster test)
        if tar -xzf "$LATEST_BACKUP" -C "$TEST_DIR/extract_test" 2>/dev/null --wildcards "*.md" --wildcards "*.sh" | head -10; then
            FILES_EXTRACTED=$(find "$TEST_DIR/extract_test" -type f | wc -l)
            echo -e "${GREEN}✓ Successfully extracted $FILES_EXTRACTED sample files${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))

            cat >> "$TEST_REPORT" <<EOF
### Partial Extraction: PASS

- **Files Extracted:** $FILES_EXTRACTED
- **Test Directory:** $TEST_DIR/extract_test

EOF
        else
            echo -e "${RED}✗ Failed to extract files${NC}"
            log_error "Extraction failed for: $LATEST_BACKUP"
            TESTS_FAILED=$((TESTS_FAILED + 1))

            cat >> "$TEST_REPORT" <<EOF
### Partial Extraction: FAIL

**ERROR:** Could not extract files from backup archive.

EOF
        fi
    elif [[ "$LATEST_BACKUP" == *.zip ]]; then
        if unzip -q "$LATEST_BACKUP" "*.md" "*.sh" -d "$TEST_DIR/extract_test" 2>/dev/null; then
            FILES_EXTRACTED=$(find "$TEST_DIR/extract_test" -type f | wc -l)
            echo -e "${GREEN}✓ Successfully extracted $FILES_EXTRACTED sample files${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ Failed to extract files${NC}"
            log_error "Extraction failed for: $LATEST_BACKUP"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no backup found)${NC}"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
fi

#═══════════════════════════════════════════════════════════════
# TEST 4: Verify Critical Files Present
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[4/7] Checking for critical files in backup...${NC}"

if [ -n "$LATEST_BACKUP" ] && [ -d "$TEST_DIR/extract_test" ]; then
    log "Verifying critical files"

    # List of critical files to check for (adjust for your system)
    CRITICAL_FILES=(
        "*.md"
        "*.sh"
        "*.py"
        ".gitignore"
        "README*"
    )

    CRITICAL_FOUND=0
    CRITICAL_MISSING=0

    for pattern in "${CRITICAL_FILES[@]}"; do
        if find "$TEST_DIR/extract_test" -name "$pattern" 2>/dev/null | grep -q .; then
            CRITICAL_FOUND=$((CRITICAL_FOUND + 1))
        else
            CRITICAL_MISSING=$((CRITICAL_MISSING + 1))
        fi
    done

    if [ "$CRITICAL_FOUND" -gt 0 ]; then
        echo -e "${GREEN}✓ Found $CRITICAL_FOUND types of critical files${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Critical Files Check: PASS

- **File Types Found:** $CRITICAL_FOUND
- **File Types Missing:** $CRITICAL_MISSING

EOF
    else
        echo -e "${YELLOW}⚠ No critical files found in sample${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⊘ Skipped (extraction failed)${NC}"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
fi

#═══════════════════════════════════════════════════════════════
# TEST 5: Backup Age Check
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[5/7] Checking backup age...${NC}"

if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_AGE_DAYS=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 86400 ))

    log "Backup age: $BACKUP_AGE_DAYS days"

    if [ "$BACKUP_AGE_DAYS" -le 1 ]; then
        echo -e "${GREEN}✓ Backup is recent ($BACKUP_AGE_DAYS days old)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Age: EXCELLENT

Backup is $BACKUP_AGE_DAYS days old (within 24 hours).

EOF
    elif [ "$BACKUP_AGE_DAYS" -le 7 ]; then
        echo -e "${GREEN}✓ Backup is acceptable ($BACKUP_AGE_DAYS days old)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Age: GOOD

Backup is $BACKUP_AGE_DAYS days old (within 1 week).

EOF
    elif [ "$BACKUP_AGE_DAYS" -le 30 ]; then
        echo -e "${YELLOW}⚠ Backup is old ($BACKUP_AGE_DAYS days)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Age: WARNING

Backup is $BACKUP_AGE_DAYS days old. Consider running a fresh backup.

EOF
    else
        echo -e "${RED}✗ Backup is very old ($BACKUP_AGE_DAYS days)${NC}"
        log_error "Backup is too old: $BACKUP_AGE_DAYS days"
        TESTS_FAILED=$((TESTS_FAILED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Age: CRITICAL

**WARNING:** Backup is $BACKUP_AGE_DAYS days old. Run a fresh backup immediately.

EOF
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no backup found)${NC}"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
fi

#═══════════════════════════════════════════════════════════════
# TEST 6: Backup Size Check
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[6/7] Checking backup size...${NC}"

if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_SIZE_BYTES=$(stat -c %s "$LATEST_BACKUP")
    BACKUP_SIZE_MB=$((BACKUP_SIZE_BYTES / 1024 / 1024))

    log "Backup size: ${BACKUP_SIZE_MB}MB"

    if [ "$BACKUP_SIZE_BYTES" -gt 1000 ]; then
        echo -e "${GREEN}✓ Backup size is reasonable (${BACKUP_SIZE_MB}MB)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Size: PASS

- **Size:** ${BACKUP_SIZE_MB}MB
- **Bytes:** $BACKUP_SIZE_BYTES

EOF
    else
        echo -e "${RED}✗ Backup size is suspiciously small (${BACKUP_SIZE_MB}MB)${NC}"
        log_error "Backup size is too small: ${BACKUP_SIZE_MB}MB"
        TESTS_FAILED=$((TESTS_FAILED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Size: FAIL

**WARNING:** Backup size (${BACKUP_SIZE_MB}MB) seems too small. Backup may be incomplete.

EOF
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no backup found)${NC}"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
fi

#═══════════════════════════════════════════════════════════════
# TEST 7: Backup Rotation Check
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[7/7] Checking backup rotation...${NC}"

if [ -d "$BACKUP_DIR" ] || [ -d "$GDRIVE_BACKUP" ]; then
    BACKUP_COUNT=0

    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.tar.gz" -o -name "*.zip" | wc -l)
    fi

    if [ -d "$GDRIVE_BACKUP" ]; then
        GDRIVE_COUNT=$(find "$GDRIVE_BACKUP" -name "*.tar.gz" -o -name "*.zip" | wc -l)
        BACKUP_COUNT=$((BACKUP_COUNT + GDRIVE_COUNT))
    fi

    log "Total backups found: $BACKUP_COUNT"

    if [ "$BACKUP_COUNT" -ge 3 ]; then
        echo -e "${GREEN}✓ Multiple backups available ($BACKUP_COUNT total)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Rotation: EXCELLENT

- **Total Backups:** $BACKUP_COUNT
- **Status:** Multiple restore points available

EOF
    elif [ "$BACKUP_COUNT" -ge 1 ]; then
        echo -e "${YELLOW}⚠ Only $BACKUP_COUNT backup(s) found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))

        cat >> "$TEST_REPORT" <<EOF
### Backup Rotation: WARNING

- **Total Backups:** $BACKUP_COUNT
- **Recommendation:** Keep at least 3-7 backup versions for safety

EOF
    else
        echo -e "${RED}✗ No backups found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⊘ Backup directories not found${NC}"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
fi

#═══════════════════════════════════════════════════════════════
# GENERATE SUMMARY
#═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}       Verification Complete - Summary     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
if [ "$TOTAL_TESTS" -gt 0 ]; then
    PASS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))
else
    PASS_RATE=0
fi

echo -e "${GREEN}  PASSED:  $TESTS_PASSED${NC}"
echo -e "${RED}  FAILED:  $TESTS_FAILED${NC}"
echo -e "  SKIPPED: $TESTS_SKIPPED"
echo ""
echo -e "  PASS RATE: ${PASS_RATE}%"
echo ""

# Update report summary
sed -i "s/^## Summary$/## Summary\n\n**Test Results:**\n- Passed: $TESTS_PASSED\n- Failed: $TESTS_FAILED\n- Skipped: $TESTS_SKIPPED\n- Pass Rate: ${PASS_RATE}%/" "$TEST_REPORT"

# Add overall assessment
cat >> "$TEST_REPORT" <<EOF

---

## Overall Assessment

EOF

if [ "$TESTS_FAILED" -eq 0 ]; then
    cat >> "$TEST_REPORT" <<EOF
**Status:** 🟢 EXCELLENT

All backup verification tests passed. Your backups are healthy and restorable.

EOF
    echo -e "${GREEN}Status: EXCELLENT - Backups are healthy${NC}"
elif [ "$PASS_RATE" -ge 70 ]; then
    cat >> "$TEST_REPORT" <<EOF
**Status:** 🟡 WARNING

Some backup tests failed. Review the failures above and address them.

EOF
    echo -e "${YELLOW}Status: WARNING - Some issues found${NC}"
else
    cat >> "$TEST_REPORT" <<EOF
**Status:** 🔴 CRITICAL

Multiple backup tests failed. Your backup system needs immediate attention.

EOF
    echo -e "${RED}Status: CRITICAL - Backup system needs attention${NC}"
fi

cat >> "$TEST_REPORT" <<EOF

---

## Recommendations

1. **Run backups daily** - Ensure automated backups are scheduled
2. **Test restores monthly** - Run this script on the 1st of each month
3. **Keep multiple versions** - Maintain at least 7 daily backups
4. **Monitor backup age** - Backups older than 7 days are a risk
5. **Verify storage space** - Ensure backup locations have adequate space

---

## Next Test

**Recommended:** $(date -d "+30 days" +%Y-%m-%d)

---

*Generated by Skippy Backup Verification Test*
*Report Location:* $TEST_REPORT
EOF

echo -e "${GREEN}Report saved to:${NC} $TEST_REPORT"
echo ""

# Send email notification if configured
if [ "$SEND_EMAIL" = true ] && command -v mail &> /dev/null; then
    if [ "$TESTS_FAILED" -gt 0 ]; then
        mail -s "⚠️ Backup Verification: ${TESTS_FAILED} Tests Failed" "$NOTIFY_EMAIL" < "$TEST_REPORT"
        log "Email notification sent to $NOTIFY_EMAIL"
    fi
fi

log "Backup verification complete. Pass rate: ${PASS_RATE}%"

# Exit with appropriate code
if [ "$TESTS_FAILED" -gt 0 ]; then
    exit 1
else
    exit 0
fi
