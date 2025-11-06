#!/bin/bash
# Health Check Script
# Version: 1.0.0
# Purpose: Comprehensive system health monitoring
# Usage: ./health_check_v1.0.0.sh [--json] [--nagios]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
OUTPUT_FORMAT="${1:-text}"
HEALTH_CHECK_DIR="/var/log/skippy/health"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Thresholds
CPU_WARNING=75
CPU_CRITICAL=90
MEM_WARNING=80
MEM_CRITICAL=95
DISK_WARNING=80
DISK_CRITICAL=95

# Health status
HEALTH_STATUS="healthy"
WARNINGS=()
CRITICAL=()
CHECKS_PASSED=0
CHECKS_FAILED=0

# Create health check directory
mkdir -p "${HEALTH_CHECK_DIR}"

#######################################
# Helper Functions
#######################################

log_check() {
    local check_name="$1"
    local status="$2"
    local message="$3"

    if [ "${status}" = "pass" ]; then
        ((CHECKS_PASSED++))
        if [ "${OUTPUT_FORMAT}" = "text" ]; then
            echo -e "${GREEN}✓${NC} ${check_name}: ${message}"
        fi
    elif [ "${status}" = "warn" ]; then
        ((CHECKS_FAILED++))
        WARNINGS+=("${check_name}: ${message}")
        HEALTH_STATUS="warning"
        if [ "${OUTPUT_FORMAT}" = "text" ]; then
            echo -e "${YELLOW}⚠${NC} ${check_name}: ${message}"
        fi
    elif [ "${status}" = "fail" ]; then
        ((CHECKS_FAILED++))
        CRITICAL+=("${check_name}: ${message}")
        HEALTH_STATUS="critical"
        if [ "${OUTPUT_FORMAT}" = "text" ]; then
            echo -e "${RED}✗${NC} ${check_name}: ${message}"
        fi
    fi
}

#######################################
# Health Checks
#######################################

check_cpu() {
    if command -v mpstat >/dev/null 2>&1; then
        CPU_IDLE=$(mpstat 1 1 | tail -1 | awk '{print $NF}')
        CPU_USED=$(echo "100 - ${CPU_IDLE}" | bc)
    else
        # Fallback using top
        CPU_USED=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    fi

    CPU_USED_INT=${CPU_USED%.*}

    if [ "${CPU_USED_INT}" -ge "${CPU_CRITICAL}" ]; then
        log_check "CPU Usage" "fail" "${CPU_USED}% (critical threshold: ${CPU_CRITICAL}%)"
    elif [ "${CPU_USED_INT}" -ge "${CPU_WARNING}" ]; then
        log_check "CPU Usage" "warn" "${CPU_USED}% (warning threshold: ${CPU_WARNING}%)"
    else
        log_check "CPU Usage" "pass" "${CPU_USED}%"
    fi
}

check_memory() {
    if command -v free >/dev/null 2>&1; then
        MEM_PERCENT=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
        MEM_PERCENT_INT=${MEM_PERCENT%.*}
        MEM_USED=$(free -h | grep Mem | awk '{print $3}')
        MEM_TOTAL=$(free -h | grep Mem | awk '{print $2}')

        if [ "${MEM_PERCENT_INT}" -ge "${MEM_CRITICAL}" ]; then
            log_check "Memory Usage" "fail" "${MEM_PERCENT_INT}% (${MEM_USED}/${MEM_TOTAL}, critical: ${MEM_CRITICAL}%)"
        elif [ "${MEM_PERCENT_INT}" -ge "${MEM_WARNING}" ]; then
            log_check "Memory Usage" "warn" "${MEM_PERCENT_INT}% (${MEM_USED}/${MEM_TOTAL}, warning: ${MEM_WARNING}%)"
        else
            log_check "Memory Usage" "pass" "${MEM_PERCENT_INT}% (${MEM_USED}/${MEM_TOTAL})"
        fi
    else
        log_check "Memory Usage" "warn" "Cannot check (free not available)"
    fi
}

check_disk() {
    DISK_PERCENT=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    DISK_USED=$(df -h / | tail -1 | awk '{print $3}')
    DISK_TOTAL=$(df -h / | tail -1 | awk '{print $2}')

    if [ "${DISK_PERCENT}" -ge "${DISK_CRITICAL}" ]; then
        log_check "Disk Usage" "fail" "${DISK_PERCENT}% (${DISK_USED}/${DISK_TOTAL}, critical: ${DISK_CRITICAL}%)"
    elif [ "${DISK_PERCENT}" -ge "${DISK_WARNING}" ]; then
        log_check "Disk Usage" "warn" "${DISK_PERCENT}% (${DISK_USED}/${DISK_TOTAL}, warning: ${DISK_WARNING}%)"
    else
        log_check "Disk Usage" "pass" "${DISK_PERCENT}% (${DISK_USED}/${DISK_TOTAL})"
    fi
}

check_load_average() {
    if command -v uptime >/dev/null 2>&1; then
        LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
        CPU_COUNT=$(nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo)

        # Load average threshold is number of CPUs
        LOAD_THRESHOLD=$(echo "${CPU_COUNT} * 2" | bc)

        if (( $(echo "${LOAD_AVG} > ${LOAD_THRESHOLD}" | bc -l) )); then
            log_check "Load Average" "warn" "${LOAD_AVG} (${CPU_COUNT} CPUs, threshold: ${LOAD_THRESHOLD})"
        else
            log_check "Load Average" "pass" "${LOAD_AVG} (${CPU_COUNT} CPUs)"
        fi
    else
        log_check "Load Average" "warn" "Cannot check (uptime not available)"
    fi
}

check_config() {
    if [ -f "config.env" ]; then
        log_check "Configuration" "pass" "config.env exists"
    else
        log_check "Configuration" "fail" "config.env not found"
        return
    fi

    # Check required variables
    source config.env 2>/dev/null || true

    REQUIRED_VARS=("SKIPPY_BASE_PATH" "WORDPRESS_BASE_PATH" "EBON_HOST")
    MISSING_VARS=()

    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var:-}" ]; then
            MISSING_VARS+=("${var}")
        fi
    done

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        log_check "Required Variables" "fail" "Missing: ${MISSING_VARS[*]}"
    else
        log_check "Required Variables" "pass" "All present"
    fi
}

check_ssh_connectivity() {
    if [ -f "config.env" ]; then
        source config.env 2>/dev/null || true

        if [ -n "${EBON_HOST:-}" ]; then
            if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no "${EBON_HOST}" "echo 'OK'" >/dev/null 2>&1; then
                log_check "SSH Connectivity" "pass" "Connection to ${EBON_HOST} successful"
            else
                log_check "SSH Connectivity" "warn" "Cannot connect to ${EBON_HOST}"
            fi
        else
            log_check "SSH Connectivity" "warn" "EBON_HOST not configured"
        fi
    fi
}

check_python_dependencies() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        log_check "Python" "pass" "v${PYTHON_VERSION}"

        # Check for key dependencies
        MISSING_DEPS=()
        for dep in psutil httpx paramiko; do
            if ! python3 -c "import ${dep}" 2>/dev/null; then
                MISSING_DEPS+=("${dep}")
            fi
        done

        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            log_check "Python Dependencies" "warn" "Missing: ${MISSING_DEPS[*]}"
        else
            log_check "Python Dependencies" "pass" "All installed"
        fi
    else
        log_check "Python" "fail" "python3 not found"
    fi
}

check_mcp_server() {
    if pgrep -f "mcp-servers/general-server/server.py" >/dev/null; then
        log_check "MCP Server" "pass" "Running"
    else
        log_check "MCP Server" "warn" "Not running"
    fi
}

check_wordpress() {
    if [ -f "config.env" ]; then
        source config.env 2>/dev/null || true

        if [ -n "${WORDPRESS_BASE_PATH:-}" ]; then
            if ssh -o ConnectTimeout=5 -o BatchMode=yes "${EBON_HOST}" "[ -f '${WORDPRESS_BASE_PATH}/wp-config.php' ]" 2>/dev/null; then
                log_check "WordPress" "pass" "wp-config.php found at ${WORDPRESS_BASE_PATH}"
            else
                log_check "WordPress" "warn" "wp-config.php not found at ${WORDPRESS_BASE_PATH}"
            fi
        else
            log_check "WordPress" "warn" "WORDPRESS_BASE_PATH not configured"
        fi
    fi
}

check_backups() {
    BACKUP_DIR="/tmp/skippy_backups"
    if [ -d "${BACKUP_DIR}" ]; then
        BACKUP_COUNT=$(find "${BACKUP_DIR}" -type f -name "*.tar.gz" -mtime -7 | wc -l)
        if [ "${BACKUP_COUNT}" -gt 0 ]; then
            log_check "Recent Backups" "pass" "${BACKUP_COUNT} backups in last 7 days"
        else
            log_check "Recent Backups" "warn" "No backups in last 7 days"
        fi
    else
        log_check "Recent Backups" "warn" "Backup directory not found"
    fi
}

#######################################
# Main Execution
#######################################

if [ "${OUTPUT_FORMAT}" = "text" ]; then
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}  Skippy System Health Check${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo ""
fi

# Run all checks
check_cpu
check_memory
check_disk
check_load_average
check_config
check_ssh_connectivity
check_python_dependencies
check_mcp_server
check_wordpress
check_backups

# Summary
if [ "${OUTPUT_FORMAT}" = "text" ]; then
    echo ""
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}  Health Check Summary${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo ""
    echo "Status: ${HEALTH_STATUS^^}"
    echo "Checks Passed: ${CHECKS_PASSED}"
    echo "Checks Failed: ${CHECKS_FAILED}"
    echo ""

    if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo -e "${YELLOW}Warnings:${NC}"
        for warning in "${WARNINGS[@]}"; do
            echo "  - ${warning}"
        done
        echo ""
    fi

    if [ ${#CRITICAL[@]} -gt 0 ]; then
        echo -e "${RED}Critical Issues:${NC}"
        for issue in "${CRITICAL[@]}"; do
            echo "  - ${issue}"
        done
        echo ""
    fi

    if [ "${HEALTH_STATUS}" = "healthy" ]; then
        echo -e "${GREEN}✓ All systems operational${NC}"
    fi
    echo ""
elif [ "${OUTPUT_FORMAT}" = "--json" ]; then
    # JSON output
    cat <<EOF
{
  "status": "${HEALTH_STATUS}",
  "checks_passed": ${CHECKS_PASSED},
  "checks_failed": ${CHECKS_FAILED},
  "warnings": [$(printf '"%s",' "${WARNINGS[@]}" | sed 's/,$//')]
  "critical": [$(printf '"%s",' "${CRITICAL[@]}" | sed 's/,$//')]
  "timestamp": "$(date -Iseconds)"
}
EOF
elif [ "${OUTPUT_FORMAT}" = "--nagios" ]; then
    # Nagios-compatible output
    if [ "${HEALTH_STATUS}" = "healthy" ]; then
        echo "OK - All health checks passed (${CHECKS_PASSED}/${CHECKS_PASSED})"
        exit 0
    elif [ "${HEALTH_STATUS}" = "warning" ]; then
        echo "WARNING - ${#WARNINGS[@]} warnings detected | passed=${CHECKS_PASSED} failed=${CHECKS_FAILED}"
        exit 1
    else
        echo "CRITICAL - ${#CRITICAL[@]} critical issues detected | passed=${CHECKS_PASSED} failed=${CHECKS_FAILED}"
        exit 2
    fi
fi

# Save health report
REPORT_FILE="${HEALTH_CHECK_DIR}/health_${TIMESTAMP}.log"
{
    echo "Health Check Report - ${TIMESTAMP}"
    echo "Status: ${HEALTH_STATUS}"
    echo "Passed: ${CHECKS_PASSED}"
    echo "Failed: ${CHECKS_FAILED}"
    echo ""
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo "Warnings:"
        printf '  - %s\n' "${WARNINGS[@]}"
    fi
    if [ ${#CRITICAL[@]} -gt 0 ]; then
        echo "Critical:"
        printf '  - %s\n' "${CRITICAL[@]}"
    fi
} > "${REPORT_FILE}"

# Exit code
if [ "${HEALTH_STATUS}" = "healthy" ]; then
    exit 0
elif [ "${HEALTH_STATUS}" = "warning" ]; then
    exit 1
else
    exit 2
fi
