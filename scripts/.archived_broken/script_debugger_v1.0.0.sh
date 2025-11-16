#!/bin/bash
# Shell Script Debugger v1.0.0
# Debug and analyze bash scripts
# Part of: Skippy Enhancement Project - TIER 2
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
DEBUG_REPORTS="${SKIPPY_BASE}/conversations/debug_reports"

usage() {
    cat <<EOF
Shell Script Debugger v1.0.0

USAGE:
    $0 <command> <script> [options]

COMMANDS:
    syntax <script>              Check syntax errors
    analyze <script>             Deep analysis (shellcheck)
    trace <script> [args]        Run with trace enabled
    profile <script> [args]      Profile execution time
    lint <script>                Check code style and best practices
    find-issues <script>         Find common issues
    fix <script>                 Auto-fix common issues
    explain <script> <line>      Explain what line does
    full-debug <script>          Complete debugging suite

OPTIONS:
    --fix                        Auto-fix issues when possible
    --report                     Generate detailed report

EXAMPLES:
    # Check syntax
    $0 syntax my_script.sh

    # Analyze with shellcheck
    $0 analyze my_script.sh

    # Run with trace
    $0 trace my_script.sh arg1 arg2

    # Profile performance
    $0 profile slow_script.sh

    # Find and fix issues
    $0 fix my_script.sh

    # Complete debug
    $0 full-debug problem_script.sh

EOF
    exit 1
}

# Parse options
AUTOFIX=false
GENERATE_REPORT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fix)
            AUTOFIX=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"
SCRIPT="${2:-}"

if [ -z "$COMMAND" ] || [ -z "$SCRIPT" ]; then
    usage
fi

# Ensure script exists
if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}✗ Script not found: $SCRIPT${NC}"
    exit 1
fi

mkdir -p "$DEBUG_REPORTS"

# Report file
if [ "$GENERATE_REPORT" = true ]; then
    REPORT_FILE="${DEBUG_REPORTS}/debug_$(basename "$SCRIPT")_$(date +%Y%m%d_%H%M%S).md"
    cat > "$REPORT_FILE" <<EOF
# Script Debug Report

**Script:** $SCRIPT
**Date:** $(date)
**Command:** $COMMAND

---

## Analysis Results

EOF
fi

log() {
    echo -e "${BLUE}$1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "$1" >> "$REPORT_FILE"
    fi
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "✓ $1" >> "$REPORT_FILE"
    fi
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "⚠ $1" >> "$REPORT_FILE"
    fi
}

error() {
    echo -e "${RED}✗ $1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "✗ $1" >> "$REPORT_FILE"
    fi
}

# Check syntax
check_syntax() {
    log "Checking syntax..."

    if bash -n "$SCRIPT" 2>&1; then
        success "No syntax errors"
        return 0
    else
        local errors=$(bash -n "$SCRIPT" 2>&1)
        error "Syntax errors found:"
        echo "$errors"
        if [ "$GENERATE_REPORT" = true ]; then
            echo "\`\`\`" >> "$REPORT_FILE"
            echo "$errors" >> "$REPORT_FILE"
            echo "\`\`\`" >> "$REPORT_FILE"
        fi
        return 1
    fi
}

# Analyze with shellcheck
analyze_script() {
    log "Running deep analysis..."

    if ! command -v shellcheck &> /dev/null; then
        warning "shellcheck not installed"
        echo "Install: sudo apt install shellcheck"
        return 1
    fi

    local analysis=$(shellcheck "$SCRIPT" 2>&1 || true)

    if [ -z "$analysis" ]; then
        success "No issues found by shellcheck"
        return 0
    else
        warning "ShellCheck found issues:"
        echo "$analysis"

        if [ "$GENERATE_REPORT" = true ]; then
            cat >> "$REPORT_FILE" <<EOF

### ShellCheck Analysis

\`\`\`
$analysis
\`\`\`

EOF
        fi
        return 1
    fi
}

# Run with trace
trace_script() {
    log "Running with trace enabled..."

    shift 2  # Remove command and script from args

    echo -e "${CYAN}═══ Trace Output ═══${NC}"
    bash -x "$SCRIPT" "$@" 2>&1 | tee /tmp/trace_output.log

    if [ "$GENERATE_REPORT" = true ]; then
        cat >> "$REPORT_FILE" <<EOF

### Trace Output

\`\`\`bash
$(cat /tmp/trace_output.log)
\`\`\`

EOF
    fi

    success "Trace complete"
}

# Profile execution
profile_script() {
    log "Profiling script execution..."

    shift 2  # Remove command and script

    local start_time=$(date +%s%N)

    # Run with time tracking
    PS4='+ $(date "+%s.%N")\011 ' bash -x "$SCRIPT" "$@" 2> /tmp/profile_trace.log

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))  # Convert to ms

    success "Total execution time: ${duration}ms"

    # Analyze which lines took longest
    log "Top 10 slowest operations:"

    awk '{
        if (NF >= 2) {
            time = $1
            cmd = ""
            for (i=2; i<=NF; i++) cmd = cmd " " $i
            print time, cmd
        }
    }' /tmp/profile_trace.log | \
    awk 'NR>1 {print ($1-prev), line; prev=$1; line=$0} {prev=$1; line=$0}' | \
    sort -rn | head -10

    if [ "$GENERATE_REPORT" = true ]; then
        cat >> "$REPORT_FILE" <<EOF

### Performance Profile

**Total Time:** ${duration}ms

**Slowest Operations:**
\`\`\`
$(awk '{if (NF >= 2) {time = $1; cmd = ""; for (i=2; i<=NF; i++) cmd = cmd " " $i; print time, cmd}}' /tmp/profile_trace.log | \
    awk 'NR>1 {print ($1-prev), line; prev=$1; line=$0} {prev=$1; line=$0}' | \
    sort -rn | head -10)
\`\`\`

EOF
    fi
}

# Lint script
lint_script() {
    log "Checking code style..."

    local issues=0

    # Check for missing shebang
    if ! head -1 "$SCRIPT" | grep -q '^#!/'; then
        warning "Missing shebang (#!/bin/bash)"
        ((issues++))
    fi

    # Check for set -e
    if ! grep -q 'set -e' "$SCRIPT"; then
        warning "Missing 'set -e' (exit on error)"
        ((issues++))
    fi

    # Check for set -u
    if ! grep -q 'set -u' "$SCRIPT"; then
        warning "Missing 'set -u' (error on undefined variable)"
        ((issues++))
    fi

    # Check for set -o pipefail
    if ! grep -q 'set -o pipefail' "$SCRIPT"; then
        warning "Missing 'set -o pipefail'"
        ((issues++))
    fi

    # Check for functions without local variables
    if grep -q '^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*()' "$SCRIPT"; then
        log "Checking function variable scoping..."
        if ! grep -q 'local ' "$SCRIPT"; then
            warning "Functions found but no 'local' variables used"
            ((issues++))
        fi
    fi

    # Check for unquoted variables
    local unquoted=$(grep -n '\$[A-Za-z_][A-Za-z0-9_]*[^"]' "$SCRIPT" | grep -v '"$' | head -5 || true)
    if [ -n "$unquoted" ]; then
        warning "Potentially unquoted variables found:"
        echo "$unquoted"
        ((issues++))
    fi

    if [ $issues -eq 0 ]; then
        success "No style issues found"
    else
        warning "Found $issues style issues"
    fi

    return $issues
}

# Find common issues
find_issues() {
    log "Scanning for common issues..."

    local issues=0

    # Check for dangerous patterns
    if grep -q 'rm -rf /' "$SCRIPT"; then
        error "DANGEROUS: Found 'rm -rf /' command"
        ((issues++))
    fi

    # Check for eval usage
    if grep -q 'eval ' "$SCRIPT"; then
        warning "Found 'eval' usage (potential security risk)"
        ((issues++))
    fi

    # Check for hardcoded passwords
    if grep -qE '(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']' "$SCRIPT"; then
        warning "Possible hardcoded password found"
        ((issues++))
    fi

    # Check for missing error handling
    if ! grep -q 'trap' "$SCRIPT" && ! grep -q 'set -e' "$SCRIPT"; then
        warning "No error handling detected"
        ((issues++))
    fi

    # Check for command substitution without quotes
    if grep -qE "\\$\\([^)]+\\)[^\"]" "$SCRIPT" 2>/dev/null; then
        warning "Command substitution might need quoting"
        ((issues++))
    fi

    # Check for missing function documentation
    local func_pattern='^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*\(\)'
    if grep -q "$func_pattern" "$SCRIPT"; then
        local funcs=$(grep -c "$func_pattern" "$SCRIPT")
        local comments=$(grep -c '^[[:space:]]*#.*function\|^[[:space:]]*#.*Function' "$SCRIPT" || echo 0)

        if [ "$funcs" -gt "$comments" ]; then
            warning "Some functions missing documentation comments"
            ((issues++))
        fi
    fi

    if [ $issues -eq 0 ]; then
        success "No common issues found"
    else
        warning "Found $issues potential issues"
    fi

    return $issues
}

# Auto-fix common issues
fix_issues() {
    log "Auto-fixing common issues..."

    local backup="${SCRIPT}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$SCRIPT" "$backup"
    success "Created backup: $backup"

    local temp=$(mktemp)

    # Add shebang if missing
    if ! head -1 "$SCRIPT" | grep -q '^#!/'; then
        echo '#!/bin/bash' > "$temp"
        cat "$SCRIPT" >> "$temp"
        mv "$temp" "$SCRIPT"
        success "Added shebang"
    fi

    # Add error handling if missing
    if ! grep -q 'set -euo pipefail' "$SCRIPT"; then
        local temp2=$(mktemp)
        head -1 "$SCRIPT" > "$temp2"
        echo 'set -euo pipefail' >> "$temp2"
        tail -n +2 "$SCRIPT" >> "$temp2"
        mv "$temp2" "$SCRIPT"
        success "Added 'set -euo pipefail'"
    fi

    success "Auto-fix complete"
    echo "Backup saved to: $backup"
}

# Explain what a line does
explain_line() {
    local line_num="$3"

    if [ -z "$line_num" ]; then
        error "Line number required"
        usage
    fi

    log "Explaining line $line_num..."

    local line=$(sed -n "${line_num}p" "$SCRIPT")

    if [ -z "$line" ]; then
        error "Line $line_num not found in script"
        exit 1
    fi

    echo -e "${CYAN}Line $line_num:${NC}"
    echo "$line"
    echo
    echo -e "${BLUE}Explanation:${NC}"

    # Simple pattern matching for common commands
    case "$line" in
        *"set -e"*)
            echo "Exit immediately if any command returns non-zero status"
            ;;
        *"set -u"*)
            echo "Treat unset variables as an error"
            ;;
        *"set -o pipefail"*)
            echo "Return value of pipeline is the value of the last command to exit with non-zero status"
            ;;
        *"trap"*)
            echo "Execute command when shell receives specified signal"
            ;;
        *"local "*)
            echo "Declare local variable (function scope only)"
            ;;
        *"readonly "*)
            echo "Declare read-only variable (cannot be changed)"
            ;;
        *"$(\"*\"|'*')"*)
            echo "Command substitution - execute command and use its output"
            ;;
        *">>"*)
            echo "Append output to file"
            ;;
        *">"*)
            echo "Redirect output to file (overwrite)"
            ;;
        *"|"*)
            echo "Pipe - send output of left command to input of right command"
            ;;
        *"&&"*)
            echo "Logical AND - execute right command only if left succeeds"
            ;;
        *"||"*)
            echo "Logical OR - execute right command only if left fails"
            ;;
        *)
            echo "Command execution"
            ;;
    esac
}

# Full debug suite
full_debug() {
    echo -e "${CYAN}═══ Full Debug Suite ═══${NC}"
    echo

    echo -e "${CYAN}1. Syntax Check${NC}"
    check_syntax
    echo

    echo -e "${CYAN}2. Shellcheck Analysis${NC}"
    analyze_script
    echo

    echo -e "${CYAN}3. Code Style Lint${NC}"
    lint_script
    echo

    echo -e "${CYAN}4. Common Issues Scan${NC}"
    find_issues
    echo

    echo -e "${CYAN}═══ Debug Complete ═══${NC}"

    if [ "$GENERATE_REPORT" = true ]; then
        success "Report generated: $REPORT_FILE"
    fi
}

# Main command dispatcher
case "$COMMAND" in
    syntax)
        check_syntax
        ;;
    analyze)
        analyze_script
        ;;
    trace)
        trace_script "$@"
        ;;
    profile)
        profile_script "$@"
        ;;
    lint)
        lint_script
        ;;
    find-issues)
        find_issues
        ;;
    fix)
        fix_issues
        ;;
    explain)
        explain_line "$@"
        ;;
    full-debug)
        full_debug
        ;;
    *)
        echo "Unknown command: $COMMAND"
        usage
        ;;
esac

exit 0
