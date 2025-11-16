# Performance Baseline Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Owner**: System Administration

---

## Context

This protocol establishes performance baselines for all critical systems, enabling detection of degradation, capacity planning, and informed optimization decisions.

## Purpose

- Establish measurable performance metrics
- Track performance trends over time
- Detect degradation before users notice
- Guide capacity planning decisions
- Validate optimization efforts

---

## Core Metrics to Baseline

### 1. System Resources

**CPU Usage**
```bash
# Current load
uptime | awk -F'average:' '{print $2}'

# CPU usage over time (1 minute sample)
sar -u 1 60 > cpu_baseline_$(date +%Y%m%d).txt

# Process CPU usage
top -bn1 -o %CPU | head -20
```

**Memory Usage**
```bash
# Current memory
free -h

# Memory over time
vmstat 10 6 > memory_baseline_$(date +%Y%m%d).txt

# Memory by process
ps aux --sort=-%mem | head -20 > top_memory_processes.txt
```

**Disk I/O**
```bash
# Disk performance baseline
iostat -x 1 10 > disk_io_baseline_$(date +%Y%m%d).txt

# Disk latency test
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000 oflag=dsync 2>&1 | tee disk_write_test.txt
rm /tmp/testfile
```

**Network**
```bash
# Network throughput
iperf3 -c speedtest.server.com -t 30 > network_baseline.txt

# Network latency
ping -c 100 8.8.8.8 | tail -1 > latency_baseline.txt

# Bandwidth usage
nethogs -t -c 5 > bandwidth_usage.txt
```

### 2. WordPress Performance

**Page Load Time**
```bash
# Homepage load time
curl -w "@curl-format.txt" -o /dev/null -s "http://rundaverun-local-complete-022655.local/" > homepage_timing.txt

# Create curl-format.txt:
cat > /tmp/curl-format.txt <<EOF
time_namelookup:  %{time_namelookup}s
time_connect:     %{time_connect}s
time_appconnect:  %{time_appconnect}s
time_pretransfer: %{time_pretransfer}s
time_redirect:    %{time_redirect}s
time_starttransfer: %{time_starttransfer}s
time_total:       %{time_total}s
EOF
```

**Database Performance**
```bash
# Query time baseline
wp db query "SELECT SQL_NO_CACHE * FROM wp_posts LIMIT 100" --silent --skip-column-names | wc -l
time wp db query "SELECT SQL_NO_CACHE * FROM wp_posts LIMIT 100" > db_query_baseline.txt 2>&1

# Database size
wp db size --all-tables > db_size_baseline.txt

# Slow queries (if enabled)
mysqldumpslow /var/log/mysql/mysql-slow.log > slow_query_report.txt
```

**PHP Performance**
```bash
# PHP opcache stats
php -r 'print_r(opcache_get_status());' > opcache_baseline.txt

# PHP memory limit check
php -i | grep memory_limit

# PHP execution time
time php -r 'for($i=0;$i<1000000;$i++){}'
```

### 3. Application-Specific Metrics

**Git Operations**
```bash
# Clone time baseline
time git clone --depth 1 https://github.com/user/repo.git /tmp/clone-test 2>&1 | tee git_clone_baseline.txt
rm -rf /tmp/clone-test

# Commit time
time git add . 2>&1
time git commit -m "test" --dry-run 2>&1

# Push time (measure but don't execute)
# time git push origin master
```

**MCP Server Response**
```bash
# Server startup time
time python3 -c "import server; print('MCP server module loads')" 2>&1

# API response time
time curl -X POST http://localhost:3000/api/health -H "Content-Type: application/json" 2>&1
```

---

## Baseline Collection Script

```bash
#!/bin/bash
# performance_baseline_collector_v1.0.0.sh
# Schedule: Weekly via cron

BASELINE_DIR="/home/dave/skippy/baselines/$(date +%Y%m%d)"
mkdir -p "$BASELINE_DIR"

echo "Collecting performance baselines: $(date)" | tee "$BASELINE_DIR/collection.log"

# 1. System Resources
echo "=== System Resources ===" >> "$BASELINE_DIR/collection.log"

# CPU
echo "CPU Load Average:" > "$BASELINE_DIR/cpu.txt"
uptime >> "$BASELINE_DIR/cpu.txt"
echo "" >> "$BASELINE_DIR/cpu.txt"
echo "CPU Stats (1 min sample):" >> "$BASELINE_DIR/cpu.txt"
top -bn1 -o %CPU | head -15 >> "$BASELINE_DIR/cpu.txt"

# Memory
echo "Memory Usage:" > "$BASELINE_DIR/memory.txt"
free -h >> "$BASELINE_DIR/memory.txt"
echo "" >> "$BASELINE_DIR/memory.txt"
echo "Top Memory Processes:" >> "$BASELINE_DIR/memory.txt"
ps aux --sort=-%mem | head -10 >> "$BASELINE_DIR/memory.txt"

# Disk
echo "Disk Usage:" > "$BASELINE_DIR/disk.txt"
df -h >> "$BASELINE_DIR/disk.txt"
echo "" >> "$BASELINE_DIR/disk.txt"
echo "Inode Usage:" >> "$BASELINE_DIR/disk.txt"
df -i >> "$BASELINE_DIR/disk.txt"

# 2. WordPress (if site running)
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
SITE_URL="http://rundaverun-local-complete-022655.local"

if curl -s -I "$SITE_URL" | grep -q "200 OK"; then
    echo "=== WordPress Performance ===" >> "$BASELINE_DIR/collection.log"

    # Page load times
    echo "Page Load Times:" > "$BASELINE_DIR/wordpress.txt"

    for page in "" "?page_id=105" "?page_id=106" "?page_id=107"; do
        echo "Testing: $SITE_URL/$page" >> "$BASELINE_DIR/wordpress.txt"
        curl -w "DNS: %{time_namelookup}s, Connect: %{time_connect}s, TTFB: %{time_starttransfer}s, Total: %{time_total}s\n" \
             -o /dev/null -s "$SITE_URL/$page" >> "$BASELINE_DIR/wordpress.txt"
    done

    # Database size
    echo "" >> "$BASELINE_DIR/wordpress.txt"
    echo "Database Size:" >> "$BASELINE_DIR/wordpress.txt"
    wp --path="$WP_PATH" db size --all-tables 2>/dev/null >> "$BASELINE_DIR/wordpress.txt"
else
    echo "WordPress site not running - skipping" >> "$BASELINE_DIR/collection.log"
fi

# 3. Network Performance
echo "=== Network ===" >> "$BASELINE_DIR/collection.log"
echo "Network Latency:" > "$BASELINE_DIR/network.txt"
ping -c 10 8.8.8.8 | tail -2 >> "$BASELINE_DIR/network.txt"

# 4. Git Repository
echo "=== Git Performance ===" >> "$BASELINE_DIR/collection.log"
echo "Git Status Time:" > "$BASELINE_DIR/git.txt"
time git -C /home/dave/skippy status --short 2>&1 | head -1 >> "$BASELINE_DIR/git.txt"

# 5. Storage Growth
echo "=== Storage Metrics ===" >> "$BASELINE_DIR/collection.log"
echo "Skippy Directory Sizes:" > "$BASELINE_DIR/storage.txt"
du -sh /home/dave/skippy/*/ 2>/dev/null | sort -h >> "$BASELINE_DIR/storage.txt"

# Summary
echo "" >> "$BASELINE_DIR/collection.log"
echo "=== Baseline Collection Complete ===" >> "$BASELINE_DIR/collection.log"
echo "Files created:" >> "$BASELINE_DIR/collection.log"
ls -la "$BASELINE_DIR/" >> "$BASELINE_DIR/collection.log"

echo "Baselines saved to: $BASELINE_DIR"
```

---

## Performance Thresholds

### Acceptable Ranges

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| CPU Load (1 min) | < 2.0 | 2.0 - 4.0 | > 4.0 |
| Memory Usage | < 70% | 70-85% | > 85% |
| Disk Usage | < 80% | 80-90% | > 90% |
| Page Load (TTFB) | < 1s | 1-3s | > 3s |
| DB Query Time | < 100ms | 100-500ms | > 500ms |
| Network Latency | < 50ms | 50-150ms | > 150ms |

### Setting Thresholds

```bash
# Calculate baseline thresholds from historical data
# Mean + 2 standard deviations = Warning
# Mean + 3 standard deviations = Critical

# Example: CPU load calculation
AVG_CPU=$(awk '{sum+=$1; count++} END {print sum/count}' cpu_history.txt)
STDDEV=$(awk -v avg=$AVG_CPU '{sum+=($1-avg)^2} END {print sqrt(sum/NR)}' cpu_history.txt)
WARNING_THRESHOLD=$(echo "$AVG_CPU + 2*$STDDEV" | bc)
CRITICAL_THRESHOLD=$(echo "$AVG_CPU + 3*$STDDEV" | bc)
```

---

## Trend Analysis

### Weekly Performance Report

```bash
#!/bin/bash
# performance_trend_report.sh

REPORT_FILE="/home/dave/skippy/conversations/performance_trends_$(date +%Y%m%d).md"

echo "# Performance Trend Report" > "$REPORT_FILE"
echo "**Date:** $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Compare current to baseline
CURRENT_DATE=$(date +%Y%m%d)
LAST_WEEK=$(date -d "7 days ago" +%Y%m%d)

echo "## Comparison: $LAST_WEEK vs $CURRENT_DATE" >> "$REPORT_FILE"

# CPU Trend
if [ -f "/home/dave/skippy/baselines/$LAST_WEEK/cpu.txt" ]; then
    echo "### CPU Usage" >> "$REPORT_FILE"
    echo "Last week:" >> "$REPORT_FILE"
    head -3 "/home/dave/skippy/baselines/$LAST_WEEK/cpu.txt" >> "$REPORT_FILE"
    echo "This week:" >> "$REPORT_FILE"
    uptime >> "$REPORT_FILE"
fi

# Memory Trend
if [ -f "/home/dave/skippy/baselines/$LAST_WEEK/memory.txt" ]; then
    echo "### Memory Usage" >> "$REPORT_FILE"
    echo "Last week:" >> "$REPORT_FILE"
    head -3 "/home/dave/skippy/baselines/$LAST_WEEK/memory.txt" >> "$REPORT_FILE"
    echo "This week:" >> "$REPORT_FILE"
    free -h | head -3 >> "$REPORT_FILE"
fi

# Disk Growth
if [ -f "/home/dave/skippy/baselines/$LAST_WEEK/disk.txt" ]; then
    echo "### Disk Growth" >> "$REPORT_FILE"
    LAST_USAGE=$(grep "/home" "/home/dave/skippy/baselines/$LAST_WEEK/disk.txt" | awk '{print $3}')
    CURRENT_USAGE=$(df -h /home | tail -1 | awk '{print $3}')
    echo "Last week: $LAST_USAGE" >> "$REPORT_FILE"
    echo "This week: $CURRENT_USAGE" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "## Action Items" >> "$REPORT_FILE"
echo "- [ ] Review any degradation trends" >> "$REPORT_FILE"
echo "- [ ] Address threshold violations" >> "$REPORT_FILE"
echo "- [ ] Update baselines if system changed" >> "$REPORT_FILE"

echo "Report saved: $REPORT_FILE"
```

---

## Performance Testing

### Load Testing WordPress

```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 http://rundaverun-local-complete-022655.local/ > load_test_results.txt

# Using siege
siege -c 10 -t 1M http://rundaverun-local-complete-022655.local/ 2>&1 | tee siege_results.txt

# Using wrk (modern alternative)
wrk -t4 -c100 -d30s http://rundaverun-local-complete-022655.local/
```

### Database Stress Test

```bash
# Query performance under load
for i in {1..100}; do
    time wp db query "SELECT * FROM wp_posts WHERE post_status='publish'" --silent --skip-column-names > /dev/null 2>&1
done | grep real | awk '{print $2}' > db_stress_test.txt

# Calculate average
awk -F'm' '{gsub("s","",$2); sum+=$1*60+$2; count++} END {print "Average: " sum/count "s"}' db_stress_test.txt
```

---

## Baseline Update Schedule

| System | Baseline Frequency | When to Re-baseline |
|--------|-------------------|---------------------|
| System Resources | Weekly | After hardware changes |
| WordPress | Weekly | After plugin updates, theme changes |
| Database | Monthly | After schema changes |
| Network | Monthly | After network config changes |
| Storage | Monthly | After major cleanup |

---

## Performance Optimization Checklist

When performance degrades:

1. **Compare to Baseline**
   ```bash
   # Current vs baseline
   diff "$BASELINE_DIR/cpu.txt" <(uptime)
   ```

2. **Identify Bottleneck**
   - CPU bound? → Optimize code/queries
   - Memory bound? → Increase memory/reduce cache
   - I/O bound? → SSD, caching, query optimization
   - Network bound? → CDN, compression, caching

3. **Implement Fix**
   - Apply targeted optimization
   - One change at a time

4. **Measure Impact**
   ```bash
   # Before/after comparison
   time curl http://site.local/ > /dev/null  # Before
   # Apply fix
   time curl http://site.local/ > /dev/null  # After
   ```

5. **Update Baseline**
   - If improvement is permanent
   - Document new baseline values

---

## Quick Reference

```bash
# Collect current baseline
bash /home/dave/skippy/scripts/system/performance_baseline_collector_v1.0.0.sh

# Compare to last week
diff /home/dave/skippy/baselines/YYYYMMDD/ <current>

# Page load time
curl -w "TTFB: %{time_starttransfer}s, Total: %{time_total}s\n" -o /dev/null -s http://site.local/

# Database query time
time wp db query "SELECT COUNT(*) FROM wp_posts"

# System overview
uptime && free -h && df -h /home

# Find performance hog
top -bn1 -o %CPU | head -10
```

---

## Integration with Other Protocols

- **Health Check Protocol**: Use baselines as health metrics
- **Incident Response**: Compare to baseline during incidents
- **Capacity Planning**: Project growth from trends
- **Optimization Decisions**: Validate improvements against baseline

---

**Generated**: 2025-11-16
**Status**: Active
**Next Review**: 2025-12-16
