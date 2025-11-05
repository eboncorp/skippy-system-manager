#!/bin/bash
# Performance Optimizer v1.0.0
# Analyzes and optimizes system and script performance
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
PERF_REPORTS="${SKIPPY_BASE}/conversations/performance_reports"

usage() {
    cat <<EOF
Performance Optimizer v1.0.0

USAGE:
    $0 <command> [options]

COMMANDS:
    analyze                      Analyze system performance
    profile <script>             Profile script execution
    optimize-scripts             Optimize all scripts
    optimize-wordpress           Optimize WordPress performance
    optimize-database            Optimize database queries
    cache-setup                  Setup performance caching
    benchmark                    Run performance benchmarks
    report                       Generate performance report
    recommendations              Show optimization recommendations

OPTIONS:
    --auto-fix                   Automatically apply optimizations
    --script <path>              Target specific script
    --verbose                    Verbose output

EXAMPLES:
    # Analyze system performance
    $0 analyze

    # Profile a script
    $0 profile /path/to/script.sh

    # Optimize all scripts
    $0 optimize-scripts --auto-fix

    # WordPress optimization
    $0 optimize-wordpress

    # Generate report
    $0 report

EOF
    exit 1
}

# Parse options
AUTO_FIX=false
TARGET_SCRIPT=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto-fix)
            AUTO_FIX=true
            shift
            ;;
        --script)
            TARGET_SCRIPT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"

mkdir -p "$PERF_REPORTS"

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

# Analyze system performance
analyze_performance() {
    log "Analyzing system performance..."
    echo

    local report_file="${PERF_REPORTS}/analysis_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" <<EOF
# Performance Analysis Report

**Date:** $(date)
**System:** $(hostname)

---

## System Performance

EOF

    # CPU Performance
    echo "Analyzing CPU..."
    local cpu_count=$(nproc)
    local load_avg=$(cat /proc/loadavg | awk '{print $1}')
    local load_percent=$(awk -v load="$load_avg" -v cpus="$cpu_count" 'BEGIN {printf "%.1f", (load/cpus)*100}')

    cat >> "$report_file" <<EOF
### CPU
- Cores: $cpu_count
- Load Average: $load_avg
- Load Percentage: ${load_percent}%
- Status: $([ "${load_percent%.*}" -lt 80 ] && echo "✓ Good" || echo "⚠ High")

EOF

    echo "  CPU load: ${load_percent}%"

    # Memory Performance
    echo "Analyzing memory..."
    local mem_total=$(free -m | awk '/^Mem:/ {print $2}')
    local mem_used=$(free -m | awk '/^Mem:/ {print $3}')
    local mem_percent=$(( mem_used * 100 / mem_total ))
    local mem_available=$(free -m | awk '/^Mem:/ {print $7}')

    cat >> "$report_file" <<EOF
### Memory
- Total: ${mem_total}MB
- Used: ${mem_used}MB (${mem_percent}%)
- Available: ${mem_available}MB
- Status: $([ "$mem_percent" -lt 85 ] && echo "✓ Good" || echo "⚠ High")

EOF

    echo "  Memory usage: ${mem_percent}%"

    # Disk I/O
    echo "Analyzing disk I/O..."
    local disk_usage=$(df -h "$SKIPPY_BASE" | awk 'NR==2 {print $5}' | tr -d '%')

    cat >> "$report_file" <<EOF
### Disk
- Usage: ${disk_usage}%
- Mount: $SKIPPY_BASE
- Status: $([ "$disk_usage" -lt 80 ] && echo "✓ Good" || echo "⚠ High")

EOF

    echo "  Disk usage: ${disk_usage}%"

    # Script Performance
    echo "Analyzing script performance..."
    local total_scripts=$(find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" | wc -l)
    local large_scripts=$(find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" -size +50k | wc -l)

    cat >> "$report_file" <<EOF
### Scripts
- Total: $total_scripts
- Large (>50KB): $large_scripts
- Average size: $(du -sh "${SKIPPY_BASE}/scripts" | cut -f1)

EOF

    # Recommendations
    cat >> "$report_file" <<EOF

## Recommendations

EOF

    if [ "${load_percent%.*}" -gt 80 ]; then
        echo "- ⚠ High CPU load - consider optimizing scripts" >> "$report_file"
    fi

    if [ "$mem_percent" -gt 85 ]; then
        echo "- ⚠ High memory usage - review memory-intensive processes" >> "$report_file"
    fi

    if [ "$disk_usage" -gt 80 ]; then
        echo "- ⚠ High disk usage - run cleanup: log_aggregator.sh clean" >> "$report_file"
    fi

    if [ "$large_scripts" -gt 5 ]; then
        echo "- Consider refactoring large scripts into modules" >> "$report_file"
    fi

    if [ "${load_percent%.*}" -lt 80 ] && [ "$mem_percent" -lt 85 ] && [ "$disk_usage" -lt 80 ]; then
        echo "- ✓ System performing well - no immediate action needed" >> "$report_file"
    fi

    cat >> "$report_file" <<EOF

---

*Analysis by Performance Optimizer v1.0.0*

EOF

    success "Analysis complete: $report_file"
}

# Profile script execution
profile_script() {
    local script="$1"

    if [ -z "$script" ] || [ ! -f "$script" ]; then
        error "Valid script path required"
        exit 1
    fi

    log "Profiling: $script"
    echo

    # Run with time tracking
    local start_time=$(date +%s%N)

    PS4='+ $(date +%s.%N)\011 ' bash -x "$script" 2> /tmp/profile_trace.log

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))

    echo
    log "Execution time: ${duration}ms"
    echo

    # Analyze slowest operations
    log "Top 10 slowest operations:"
    awk '{
        if (NF >= 2) {
            time = $1
            cmd = ""
            for (i=2; i<=NF; i++) cmd = cmd " " $i
            print time, cmd
        }
    }' /tmp/profile_trace.log | \
    awk 'NR>1 {print ($1-prev)*1000, line; prev=$1; line=$0} {prev=$1; line=$0}' | \
    sort -rn | head -10

    # Recommendations
    echo
    log "Optimization recommendations:"

    if [ "$duration" -gt 5000 ]; then
        warning "Script execution is slow (>5s)"
        echo "  - Consider breaking into smaller functions"
        echo "  - Cache expensive operations"
        echo "  - Reduce external command calls"
    elif [ "$duration" -gt 1000 ]; then
        echo "  - Script performance is acceptable but could be improved"
    else
        success "Script performance is good (<1s)"
    fi
}

# Optimize all scripts
optimize_scripts() {
    log "Optimizing scripts..."
    echo

    local optimized_count=0
    local total_scripts=0

    find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" | while read -r script; do
        ((total_scripts++))

        # Check for optimization opportunities
        local needs_optimization=false

        # Check for inefficient patterns
        if grep -q "cat.*|.*grep" "$script" 2>/dev/null; then
            warning "$(basename "$script"): Uses 'cat | grep' (can use grep directly)"
            needs_optimization=true
        fi

        if grep -q "ls.*|.*grep" "$script" 2>/dev/null; then
            warning "$(basename "$script"): Uses 'ls | grep' (can use find or glob)"
            needs_optimization=true
        fi

        # Check for missing command substitution optimization
        if grep -qE '\`[^`]+\`' "$script" 2>/dev/null; then
            [ "$VERBOSE" = true ] && warning "$(basename "$script"): Uses backticks (prefer \$())"
            needs_optimization=true
        fi

        if [ "$needs_optimization" = true ] && [ "$AUTO_FIX" = true ]; then
            log "  Optimizing: $(basename "$script")"
            # Create backup
            cp "$script" "${script}.backup"

            # Apply optimizations
            sed -i 's/cat \([^ ]*\) | grep/grep "" \1/g' "$script" 2>/dev/null || true

            ((optimized_count++))
        fi
    done

    echo
    if [ "$AUTO_FIX" = true ]; then
        success "Optimized $optimized_count scripts"
    else
        log "Found optimization opportunities (use --auto-fix to apply)"
    fi
}

# Optimize WordPress
optimize_wordpress() {
    log "Optimizing WordPress performance..."

    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"

    if [ ! -d "$wp_path" ]; then
        warning "WordPress not found"
        exit 1
    fi

    cd "$wp_path"

    echo

    # Database optimization
    log "Step 1: Database optimization"
    if command -v wp &> /dev/null; then
        wp db optimize
        success "Database optimized"
    fi

    # Transient cleanup
    log "Step 2: Clean transients"
    wp transient delete --all 2>/dev/null || true
    success "Transients cleaned"

    # Cache flush
    log "Step 3: Flush caches"
    wp cache flush
    success "Caches flushed"

    # Revision cleanup
    log "Step 4: Clean old revisions (keep last 5)"
    local revision_count=$(wp post list --post_type=revision --format=count)
    if [ "$revision_count" -gt 100 ]; then
        warning "Found $revision_count revisions"
        if [ "$AUTO_FIX" = true ]; then
            # Keep last 5 revisions per post
            wp config set WP_POST_REVISIONS 5 --raw
            success "Revision limit set"
        else
            echo "  Run with --auto-fix to clean"
        fi
    else
        success "Revision count OK"
    fi

    # Image optimization check
    log "Step 5: Check media library"
    local media_count=$(wp media list --format=count)
    log "  Media files: $media_count"

    # Auto-update check
    log "Step 6: Check for updates"
    local plugin_updates=$(wp plugin list --update=available --format=count)
    if [ "$plugin_updates" -gt 0 ]; then
        warning "$plugin_updates plugin updates available"
    else
        success "All plugins up to date"
    fi

    echo
    success "WordPress optimization complete"
}

# Optimize database
optimize_database() {
    log "Optimizing database..."

    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"

    if [ ! -d "$wp_path" ] || ! command -v wp &> /dev/null; then
        warning "WordPress or WP-CLI not available"
        exit 1
    fi

    cd "$wp_path"

    # Database size before
    local size_before=$(wp db size --tables 2>/dev/null || echo "0")
    log "Database size before: $size_before"

    # Optimize tables
    log "Optimizing all tables..."
    wp db optimize

    # Clean spam comments
    local spam_count=$(wp comment list --status=spam --format=count)
    if [ "$spam_count" -gt 0 ]; then
        log "Deleting $spam_count spam comments..."
        if [ "$AUTO_FIX" = true ]; then
            wp comment delete $(wp comment list --status=spam --format=ids) --force
            success "Spam comments deleted"
        else
            warning "Use --auto-fix to delete"
        fi
    fi

    # Clean trashed posts
    local trash_count=$(wp post list --post_status=trash --format=count)
    if [ "$trash_count" -gt 0 ]; then
        log "Found $trash_count trashed posts"
        if [ "$AUTO_FIX" = true ]; then
            wp post delete $(wp post list --post_status=trash --format=ids) --force
            success "Trash emptied"
        fi
    fi

    # Database size after
    local size_after=$(wp db size --tables 2>/dev/null || echo "0")
    log "Database size after: $size_after"

    success "Database optimization complete"
}

# Setup caching
setup_caching() {
    log "Setting up performance caching..."
    echo

    local cache_dir="${SKIPPY_BASE}/.cache"
    mkdir -p "$cache_dir"

    # Create cache helper functions
    cat > "${SKIPPY_BASE}/scripts/lib/cache_helper.sh" <<'EOF'
#!/bin/bash
# Cache Helper Functions
# Auto-generated by Performance Optimizer

CACHE_DIR="${SKIPPY_BASE}/.cache"
CACHE_TTL=3600  # 1 hour default

# Get cached value
cache_get() {
    local key="$1"
    local cache_file="${CACHE_DIR}/${key}.cache"

    if [ -f "$cache_file" ]; then
        local age=$(( $(date +%s) - $(stat -c %Y "$cache_file") ))
        if [ "$age" -lt "$CACHE_TTL" ]; then
            cat "$cache_file"
            return 0
        fi
    fi
    return 1
}

# Set cached value
cache_set() {
    local key="$1"
    local value="$2"
    local cache_file="${CACHE_DIR}/${key}.cache"

    echo "$value" > "$cache_file"
}

# Clear cache
cache_clear() {
    rm -f "${CACHE_DIR}"/*.cache
}
EOF

    chmod +x "${SKIPPY_BASE}/scripts/lib/cache_helper.sh"

    success "Cache helper functions created"
    log "  Location: ${SKIPPY_BASE}/scripts/lib/cache_helper.sh"
    log "  Usage in scripts:"
    echo '    source "${SKIPPY_BASE}/scripts/lib/cache_helper.sh"'
    echo '    result=$(cache_get "my_key") || {'
    echo '        result=$(expensive_operation)'
    echo '        cache_set "my_key" "$result"'
    echo '    }'
}

# Run benchmarks
run_benchmarks() {
    log "Running performance benchmarks..."
    echo

    # Benchmark script execution
    log "Benchmark 1: Script startup time"
    local startup_time=$(time (bash -c 'exit 0') 2>&1 | grep real | awk '{print $2}')
    echo "  Startup time: $startup_time"

    # Benchmark file operations
    log "Benchmark 2: File operations"
    local file_ops_start=$(date +%s%N)
    for i in {1..100}; do
        echo "test" > /tmp/bench_test_$$
        cat /tmp/bench_test_$$ > /dev/null
        rm /tmp/bench_test_$$
    done
    local file_ops_end=$(date +%s%N)
    local file_ops_time=$(( (file_ops_end - file_ops_start) / 1000000 ))
    echo "  100 file operations: ${file_ops_time}ms"

    # Benchmark JSON parsing
    if command -v jq &> /dev/null; then
        log "Benchmark 3: JSON parsing"
        local json_start=$(date +%s%N)
        for i in {1..100}; do
            echo '{"test":"value"}' | jq -r '.test' > /dev/null
        done
        local json_end=$(date +%s%N)
        local json_time=$(( (json_end - json_start) / 1000000 ))
        echo "  100 JSON operations: ${json_time}ms"
    fi

    # Benchmark WordPress (if available)
    local wp_path="/home/dave/Local Sites/rundaverun-local/app/public"
    if [ -d "$wp_path" ] && command -v wp &> /dev/null; then
        log "Benchmark 4: WordPress operations"
        cd "$wp_path"
        local wp_start=$(date +%s%N)
        wp post list --format=count > /dev/null 2>&1
        local wp_end=$(date +%s%N)
        local wp_time=$(( (wp_end - wp_start) / 1000000 ))
        echo "  WP post list: ${wp_time}ms"
    fi

    echo
    success "Benchmarks complete"
}

# Generate performance report
generate_report() {
    log "Generating comprehensive performance report..."

    local report_file="${PERF_REPORTS}/comprehensive_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" <<EOF
# Comprehensive Performance Report

**Generated:** $(date)
**System:** $(hostname)

---

## Executive Summary

EOF

    # Run quick analysis
    analyze_performance > /dev/null 2>&1

    # Add sections
    cat >> "$report_file" <<EOF

## System Metrics

$(analyze_performance 2>&1 | grep -A 20 "System Performance")

## Script Performance

- Total scripts: $(find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" | wc -l)
- Average script size: $(find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" -exec du -k {} \; | awk '{sum+=$1} END {printf "%.1fKB", sum/NR}')
- Largest scripts: $(find "${SKIPPY_BASE}/scripts" -type f -name "*.sh" -size +50k | wc -l)

## Recommendations

1. Run regular optimizations: \`performance_optimizer.sh optimize-scripts\`
2. Monitor system health: \`system_dashboard.sh live\`
3. Optimize WordPress monthly: \`performance_optimizer.sh optimize-wordpress\`
4. Profile slow scripts: \`performance_optimizer.sh profile <script>\`

---

*Report generated by Performance Optimizer v1.0.0*

EOF

    success "Report generated: $report_file"
}

# Show optimization recommendations
show_recommendations() {
    cat <<EOF
╔═══════════════════════════════════════════════════════════════╗
║           PERFORMANCE OPTIMIZATION RECOMMENDATIONS            ║
╚═══════════════════════════════════════════════════════════════╝

## System Level

1. **Monitor Resource Usage**
   - Run: system_dashboard.sh live
   - Target: CPU <80%, Memory <85%, Disk <80%

2. **Clean Up Regularly**
   - Logs: log_aggregator.sh rotate && log_aggregator.sh clean
   - Backups: Keep 30 days, archive 90 days
   - Work files: Automatic cleanup via cron

## Script Level

3. **Optimize Script Patterns**
   - Replace 'cat file | grep' with 'grep pattern file'
   - Replace 'ls | grep' with 'find' or glob patterns
   - Use \$() instead of backticks
   - Cache expensive operations

4. **Profile Slow Scripts**
   - Identify: performance_optimizer.sh profile <script>
   - Target: <1s for most operations
   - Optimize: Break into functions, reduce external calls

## WordPress Level

5. **Database Optimization**
   - Monthly: performance_optimizer.sh optimize-database --auto-fix
   - Clean revisions, spam, trash
   - Optimize tables

6. **WordPress Performance**
   - Bi-weekly: performance_optimizer.sh optimize-wordpress
   - Keep plugins updated
   - Clear transients and caches

## Caching

7. **Implement Caching**
   - Setup: performance_optimizer.sh cache-setup
   - Use cache helpers for expensive operations
   - Cache TTL: 1 hour default

## Monitoring

8. **Regular Benchmarks**
   - Monthly: performance_optimizer.sh benchmark
   - Track trends over time
   - Compare before/after optimizations

## Best Practices

- Profile before optimizing
- Measure impact of changes
- Keep functions small and focused
- Minimize external command calls
- Use built-in bash features when possible
- Cache database queries
- Clean up temporary files

EOF
}

# Main command dispatcher
case "$COMMAND" in
    analyze)
        analyze_performance
        ;;
    profile)
        profile_script "${TARGET_SCRIPT:-$2}"
        ;;
    optimize-scripts)
        optimize_scripts
        ;;
    optimize-wordpress)
        optimize_wordpress
        ;;
    optimize-database)
        optimize_database
        ;;
    cache-setup)
        setup_caching
        ;;
    benchmark)
        run_benchmarks
        ;;
    report)
        generate_report
        ;;
    recommendations)
        show_recommendations
        ;;
    *)
        usage
        ;;
esac

exit 0
