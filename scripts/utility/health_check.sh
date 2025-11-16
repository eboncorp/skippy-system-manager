#!/usr/bin/env bash
#
# Skippy System Manager - Health Check Script
# Version: 1.0.0
# Created: 2025-11-16
# Based on: robust_template.sh
#
# Performs system health checks and reports status
#

# =============================================================================
# STRICT MODE
# =============================================================================
set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# SCRIPT METADATA
# =============================================================================
readonly SCRIPT_NAME="health_check"
readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DESCRIPTION="System health check and status reporting"
readonly SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# CONFIGURATION
# =============================================================================
SKIPPY_BASE_PATH="${SKIPPY_BASE_PATH:-/home/dave/skippy}"
LOG_DIR="${SKIPPY_BASE_PATH}/logs"
LOG_FILE="${LOG_DIR}/${SCRIPT_NAME}.log"

# Thresholds
DISK_WARNING_THRESHOLD=85
DISK_CRITICAL_THRESHOLD=95
MEM_WARNING_THRESHOLD=80
MEM_CRITICAL_THRESHOLD=95
CPU_WARNING_THRESHOLD=70
CPU_CRITICAL_THRESHOLD=90

# Feature flags
VERBOSE=false
JSON_OUTPUT=false
CHECK_NETWORK=true

# =============================================================================
# COLOR OUTPUT
# =============================================================================
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m'
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly NC=''
fi

# =============================================================================
# LOGGING
# =============================================================================
setup_logging() {
    mkdir -p "$LOG_DIR" 2>/dev/null || true
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$level] $message" >> "$LOG_FILE" 2>/dev/null || true
}

log_info() {
    log "INFO" "$@"
    [[ "$VERBOSE" == "true" ]] && echo -e "${GREEN}[INFO]${NC} $*" >&2
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

check_disk_usage() {
    local path="${1:-/}"
    local usage

    usage=$(df -h "$path" | awk 'NR==2 {gsub(/%/,""); print $5}')

    if [[ "$usage" -ge "$DISK_CRITICAL_THRESHOLD" ]]; then
        echo "critical"
        log_error "Disk usage CRITICAL: ${usage}%"
    elif [[ "$usage" -ge "$DISK_WARNING_THRESHOLD" ]]; then
        echo "warning"
        log_warn "Disk usage WARNING: ${usage}%"
    else
        echo "healthy"
        log_info "Disk usage OK: ${usage}%"
    fi
}

check_memory_usage() {
    local usage

    usage=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')

    if [[ "$usage" -ge "$MEM_CRITICAL_THRESHOLD" ]]; then
        echo "critical"
        log_error "Memory usage CRITICAL: ${usage}%"
    elif [[ "$usage" -ge "$MEM_WARNING_THRESHOLD" ]]; then
        echo "warning"
        log_warn "Memory usage WARNING: ${usage}%"
    else
        echo "healthy"
        log_info "Memory usage OK: ${usage}%"
    fi
}

check_cpu_usage() {
    local usage

    usage=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}' | cut -d. -f1)

    if [[ "$usage" -ge "$CPU_CRITICAL_THRESHOLD" ]]; then
        echo "critical"
        log_error "CPU usage CRITICAL: ${usage}%"
    elif [[ "$usage" -ge "$CPU_WARNING_THRESHOLD" ]]; then
        echo "warning"
        log_warn "CPU usage WARNING: ${usage}%"
    else
        echo "healthy"
        log_info "CPU usage OK: ${usage}%"
    fi
}

check_skippy_paths() {
    local status="healthy"

    if [[ ! -d "$SKIPPY_BASE_PATH" ]]; then
        status="critical"
        log_error "Skippy base path does not exist: $SKIPPY_BASE_PATH"
    fi

    if [[ ! -d "$SKIPPY_BASE_PATH/scripts" ]]; then
        status="warning"
        log_warn "Scripts directory missing: $SKIPPY_BASE_PATH/scripts"
    fi

    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || {
            status="warning"
            log_warn "Cannot create log directory: $LOG_DIR"
        }
    fi

    echo "$status"
}

check_network_connectivity() {
    if [[ "$CHECK_NETWORK" != "true" ]]; then
        echo "skipped"
        return
    fi

    # Check internet connectivity
    if ping -c 1 -W 5 8.8.8.8 &>/dev/null; then
        log_info "Network connectivity: OK"
        echo "healthy"
    else
        log_warn "Network connectivity: No internet access"
        echo "warning"
    fi
}

# =============================================================================
# MAIN HEALTH CHECK
# =============================================================================

run_health_checks() {
    local overall_status="healthy"
    local checks_passed=0
    local checks_warning=0
    local checks_critical=0

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Skippy System Health Check${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Disk check
    echo -n "Checking disk usage... "
    disk_status=$(check_disk_usage)
    case "$disk_status" in
        healthy)
            echo -e "${GREEN}✓${NC} Healthy"
            ((checks_passed++))
            ;;
        warning)
            echo -e "${YELLOW}!${NC} Warning"
            ((checks_warning++))
            [[ "$overall_status" == "healthy" ]] && overall_status="warning"
            ;;
        critical)
            echo -e "${RED}✗${NC} Critical"
            ((checks_critical++))
            overall_status="critical"
            ;;
    esac

    # Memory check
    echo -n "Checking memory usage... "
    mem_status=$(check_memory_usage)
    case "$mem_status" in
        healthy)
            echo -e "${GREEN}✓${NC} Healthy"
            ((checks_passed++))
            ;;
        warning)
            echo -e "${YELLOW}!${NC} Warning"
            ((checks_warning++))
            [[ "$overall_status" == "healthy" ]] && overall_status="warning"
            ;;
        critical)
            echo -e "${RED}✗${NC} Critical"
            ((checks_critical++))
            overall_status="critical"
            ;;
    esac

    # CPU check
    echo -n "Checking CPU usage... "
    cpu_status=$(check_cpu_usage)
    case "$cpu_status" in
        healthy)
            echo -e "${GREEN}✓${NC} Healthy"
            ((checks_passed++))
            ;;
        warning)
            echo -e "${YELLOW}!${NC} Warning"
            ((checks_warning++))
            [[ "$overall_status" == "healthy" ]] && overall_status="warning"
            ;;
        critical)
            echo -e "${RED}✗${NC} Critical"
            ((checks_critical++))
            overall_status="critical"
            ;;
    esac

    # Skippy paths check
    echo -n "Checking Skippy paths... "
    paths_status=$(check_skippy_paths)
    case "$paths_status" in
        healthy)
            echo -e "${GREEN}✓${NC} Healthy"
            ((checks_passed++))
            ;;
        warning)
            echo -e "${YELLOW}!${NC} Warning"
            ((checks_warning++))
            [[ "$overall_status" == "healthy" ]] && overall_status="warning"
            ;;
        critical)
            echo -e "${RED}✗${NC} Critical"
            ((checks_critical++))
            overall_status="critical"
            ;;
    esac

    # Network check
    if [[ "$CHECK_NETWORK" == "true" ]]; then
        echo -n "Checking network... "
        net_status=$(check_network_connectivity)
        case "$net_status" in
            healthy)
                echo -e "${GREEN}✓${NC} Healthy"
                ((checks_passed++))
                ;;
            warning)
                echo -e "${YELLOW}!${NC} Warning"
                ((checks_warning++))
                [[ "$overall_status" == "healthy" ]] && overall_status="warning"
                ;;
            skipped)
                echo -e "${BLUE}-${NC} Skipped"
                ;;
        esac
    fi

    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo "Summary:"
    echo "  Passed: $checks_passed"
    echo "  Warnings: $checks_warning"
    echo "  Critical: $checks_critical"
    echo ""

    case "$overall_status" in
        healthy)
            echo -e "Overall Status: ${GREEN}HEALTHY${NC}"
            ;;
        warning)
            echo -e "Overall Status: ${YELLOW}WARNING${NC}"
            ;;
        critical)
            echo -e "Overall Status: ${RED}CRITICAL${NC}"
            ;;
    esac

    echo -e "${BLUE}========================================${NC}"

    log_info "Health check completed: $overall_status (passed=$checks_passed, warnings=$checks_warning, critical=$checks_critical)"

    # Exit with appropriate code
    case "$overall_status" in
        healthy) return 0 ;;
        warning) return 1 ;;
        critical) return 2 ;;
    esac
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

$SCRIPT_DESCRIPTION

Options:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -j, --json          Output results in JSON format
    --no-network        Skip network connectivity check
    --version           Show version information

Examples:
    $(basename "$0")                # Run basic health check
    $(basename "$0") -v             # Verbose output
    $(basename "$0") --no-network   # Skip network check

Exit Codes:
    0 - All checks passed (healthy)
    1 - Some checks have warnings
    2 - Critical issues found

EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -j|--json)
                JSON_OUTPUT=true
                shift
                ;;
            --no-network)
                CHECK_NETWORK=false
                shift
                ;;
            --version)
                echo "$SCRIPT_NAME v$SCRIPT_VERSION"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    setup_logging
    log_info "Starting health check v$SCRIPT_VERSION"

    run_health_checks
    local exit_code=$?

    log_info "Health check completed with exit code $exit_code"
    exit $exit_code
}

# Only run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments "$@"
    main
fi
