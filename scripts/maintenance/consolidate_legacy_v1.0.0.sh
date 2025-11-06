#!/bin/bash
# Script Consolidation Tool
# Version: 1.0.0
# Purpose: Consolidate and archive legacy scripts
# Usage: ./consolidate_legacy_v1.0.0.sh [--dry-run]

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly LEGACY_DIR="${PROJECT_ROOT}/scripts/legacy_system_managers"
readonly ARCHIVE_DIR="${PROJECT_ROOT}/scripts/archive"
readonly LOG_FILE="${PROJECT_ROOT}/logs/consolidation_$(date +%Y%m%d_%H%M%S).log"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Counters
SCRIPTS_FOUND=0
SCRIPTS_ARCHIVED=0
DUPLICATES_FOUND=0

# Dry run mode
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
fi

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

# Print colored message
print_msg() {
    local color="$1"
    shift
    echo -e "${color}$*${NC}"
}

# Main function
main() {
    print_msg "${BLUE}" "========================================"
    print_msg "${BLUE}" "  Script Consolidation Tool v1.0.0"
    print_msg "${BLUE}" "========================================"
    echo ""

    log "INFO" "Starting script consolidation"
    log "INFO" "Project root: ${PROJECT_ROOT}"
    log "INFO" "Legacy directory: ${LEGACY_DIR}"
    log "INFO" "Archive directory: ${ARCHIVE_DIR}"

    # Create log directory
    mkdir -p "$(dirname "${LOG_FILE}")"

    # Check if legacy directory exists
    if [[ ! -d "${LEGACY_DIR}" ]]; then
        print_msg "${RED}" "Error: Legacy directory not found: ${LEGACY_DIR}"
        exit 1
    fi

    # Find all scripts in legacy directory
    print_msg "${BLUE}" "Scanning for legacy scripts..."
    local scripts=()
    while IFS= read -r -d '' script; do
        scripts+=("${script}")
    done < <(find "${LEGACY_DIR}" -type f \( -name "*.py" -o -name "*.sh" \) -print0)

    SCRIPTS_FOUND=${#scripts[@]}
    log "INFO" "Found ${SCRIPTS_FOUND} scripts in legacy directory"

    if [[ ${SCRIPTS_FOUND} -eq 0 ]]; then
        print_msg "${YELLOW}" "No scripts found in legacy directory"
        exit 0
    fi

    # Analyze and categorize scripts
    print_msg "${BLUE}" "Analyzing scripts..."
    analyze_scripts "${scripts[@]}"

    # Generate report
    generate_report

    print_msg "${GREEN}" "Consolidation complete!"
    print_msg "${BLUE}" "Log file: ${LOG_FILE}"
}

# Analyze scripts
analyze_scripts() {
    local scripts=("$@")

    for script in "${scripts[@]}"; do
        local basename="$(basename "${script}")"
        local dirname="$(dirname "${script}")"

        # Check if already in archive
        if [[ "${dirname}" == *"archive"* ]]; then
            continue
        fi

        # Check for duplicates (same base name, different versions)
        check_duplicates "${script}"

        # Check last modification date
        local mod_days=$(( ($(date +%s) - $(stat -c %Y "${script}")) / 86400 ))

        if [[ ${mod_days} -gt 90 ]]; then
            log "INFO" "Script not modified in ${mod_days} days: ${basename}"

            if [[ "${DRY_RUN}" == false ]]; then
                archive_script "${script}"
            else
                log "INFO" "Would archive: ${script}"
                ((SCRIPTS_ARCHIVED++))
            fi
        fi
    done
}

# Check for duplicate scripts
check_duplicates() {
    local script="$1"
    local basename="$(basename "${script}")"
    local base_name="${basename%_v[0-9]*}"

    # Find similar scripts
    local similar_count=0
    while IFS= read -r similar; do
        if [[ "${similar}" != "${script}" ]]; then
            ((similar_count++))
        fi
    done < <(find "${LEGACY_DIR}" -name "${base_name}*" 2>/dev/null || true)

    if [[ ${similar_count} -gt 0 ]]; then
        log "WARN" "Found ${similar_count} similar versions of: ${base_name}"
        ((DUPLICATES_FOUND++))
    fi
}

# Archive a script
archive_script() {
    local script="$1"
    local basename="$(basename "${script}")"
    local rel_path="${script#${LEGACY_DIR}/}"
    local archive_path="${ARCHIVE_DIR}/consolidated_$(date +%Y%m%d)/${rel_path}"

    log "INFO" "Archiving: ${basename} -> ${archive_path}"

    # Create archive directory
    mkdir -p "$(dirname "${archive_path}")"

    # Move script
    mv "${script}" "${archive_path}"
    ((SCRIPTS_ARCHIVED++))
}

# Generate report
generate_report() {
    local report_file="${PROJECT_ROOT}/conversations/consolidation_report_$(date +%Y%m%d).md"

    cat > "${report_file}" <<EOF
# Script Consolidation Report
**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Mode**: $(if [[ "${DRY_RUN}" == true ]]; then echo "Dry Run"; else echo "Actual"; fi)

## Summary
- **Scripts Scanned**: ${SCRIPTS_FOUND}
- **Scripts Archived**: ${SCRIPTS_ARCHIVED}
- **Duplicates Found**: ${DUPLICATES_FOUND}

## Statistics
- **Archive Rate**: $(if [[ ${SCRIPTS_FOUND} -gt 0 ]]; then echo "scale=2; ${SCRIPTS_ARCHIVED} * 100 / ${SCRIPTS_FOUND}" | bc; else echo "0"; fi)%

## Recommendations
1. Review archived scripts in: ${ARCHIVE_DIR}
2. Update SCRIPT_STATUS.md with changes
3. Remove archived scripts after verification (90 day retention)
4. Consider consolidating duplicate scripts

## Next Steps
- Run tests to ensure no broken dependencies
- Update documentation
- Notify team of archived scripts

EOF

    log "INFO" "Report generated: ${report_file}"
    print_msg "${GREEN}" "Report: ${report_file}"
}

# Run main function
main
