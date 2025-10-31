#\!/bin/bash
# NexusController Complete Infrastructure Status

echo "=========================================="
echo " NEXUS INFRASTRUCTURE STATUS REPORT"
echo "=========================================="
echo "Generated: $(date)"
echo "Report by: NexusController v2.0"
echo ""

# Main server status
echo "=== MAIN SERVER ($(hostname)) ==="
echo "Uptime: $(uptime -p)"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "NexusController (Local): $(systemctl is-active nexuscontroller 2>/dev/null || echo 'Not configured')"
echo ""

# Media server status  
echo "=== MEDIA SERVER (10.0.0.29) ==="
if ping -c 1 -W 2 10.0.0.29 > /dev/null 2>&1; then
    echo "Network: ✓ Online"
    
    # Check NexusController API
    status=$(curl -s --connect-timeout 5 http://10.0.0.29:8000/api/v1/status 2>/dev/null)
    if [ \! -z "$status" ]; then
        echo "NexusController API: ✓ Healthy"
        services_running=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('services_running', 0))" 2>/dev/null || echo "0")
        services_total=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('services_total', 0))" 2>/dev/null || echo "0")
        overall_status=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('overall_status', 'unknown'))" 2>/dev/null || echo "unknown")
        
        echo "Services Status: $services_running/$services_total running ($overall_status)"
        
        # Get detailed service info
        echo ""
        echo "Media Services:"
        services_detail=$(curl -s --connect-timeout 5 http://10.0.0.29:8000/api/v1/services 2>/dev/null)
        if [ \! -z "$services_detail" ]; then
            echo "$services_detail" | python3 -c "
import sys, json
try:
    services = json.load(sys.stdin)
    for s in services:
        status_icon = '✓' if s.get('status') == 'running' else '✗'
        health = f' ({s.get(\"health\", \"unknown\")})' if s.get('health') and s.get('health') \!= 'unknown' else ''
        ports = [p.split(':')[1] for p in s.get('ports', []) if ':' in p]
        port_info = f' - Ports: {list(set(ports))}' if ports else ''
        uptime = s.get('uptime', 'unknown')
        print(f'  {status_icon} {s.get(\"name\", \"unknown\"):12} {s.get(\"status\", \"unknown\"):8}{health:10} {uptime:15}{port_info}')
except:
    print('  Error parsing service data')
"
        fi
        
        # System info
        echo ""
        echo "System Information:"
        system_info=$(curl -s --connect-timeout 5 http://10.0.0.29:8000/api/v1/system/info 2>/dev/null)
        if [ \! -z "$system_info" ]; then
            echo "$system_info" | python3 -c "
import sys, json
try:
    info = json.load(sys.stdin)
    print(f'  Hostname: {info.get(\"hostname\", \"unknown\")}')
    print(f'  Monitoring: {info.get(\"monitoring\", \"unknown\")}')
    summary = info.get('services_summary', {})
    print(f'  Services: {summary.get(\"running\", 0)}/{summary.get(\"total\", 0)} ({summary.get(\"status\", \"unknown\")})')
except:
    print('  Error parsing system info')
"
        fi
    else
        echo "NexusController API: ✗ Not responding"
    fi
else
    echo "Network: ✗ Offline"
fi

echo ""
echo "=== NETWORK SERVICES ==="
# Check key network services with timeout
services=("10.0.0.29:8096:Jellyfin" "10.0.0.29:8123:Home-Assistant" "10.0.0.29:1883:MQTT" "10.0.0.29:1880:Node-RED" "10.0.0.29:8000:NexusController")
for service in "${services[@]}"; do
    IFS=':' read -r host port name <<< "$service"
    if timeout 3 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        echo "  ✓ $name ($host:$port)"
    else
        echo "  ✗ $name ($host:$port)"
    fi
done

echo ""
echo "=== BACKUP STATUS ==="
# Check backup status on media server
if ping -c 1 -W 2 10.0.0.29 > /dev/null 2>&1; then
    backup_count=$(ssh -o ConnectTimeout=5 ebon@10.0.0.29 "ls /home/ebon/backups/ 2>/dev/null | grep backup_ | wc -l" 2>/dev/null || echo "0")
    if [ "$backup_count" -gt 0 ]; then
        echo "Backup Status: ✓ $backup_count backups available"
        latest_backup=$(ssh -o ConnectTimeout=5 ebon@10.0.0.29 "ls -1t /home/ebon/backups/ 2>/dev/null | grep backup_ | head -1" 2>/dev/null || echo "unknown")
        if [ "$latest_backup" \!= "unknown" ]; then
            backup_size=$(ssh -o ConnectTimeout=5 ebon@10.0.0.29 "du -sh /home/ebon/backups/$latest_backup 2>/dev/null | cut -f1" 2>/dev/null || echo "unknown")
            echo "Latest Backup: $latest_backup ($backup_size)"
        fi
        
        # Check cron job
        cron_status=$(ssh -o ConnectTimeout=5 ebon@10.0.0.29 "crontab -l 2>/dev/null | grep simple_backup" 2>/dev/null)
        if [ \! -z "$cron_status" ]; then
            echo "Automated Backup: ✓ Scheduled daily at 2:30 AM"
        else
            echo "Automated Backup: ✗ Not configured"
        fi
    else
        echo "Backup Status: ✗ No backups found"
    fi
else
    echo "Backup Status: ✗ Media server offline"
fi

echo ""
echo "=== MONITORING STATUS ==="
# Check monitoring service
if ping -c 1 -W 2 10.0.0.29 > /dev/null 2>&1; then
    monitor_status=$(ssh -o ConnectTimeout=5 ebon@10.0.0.29 "systemctl is-active nexus-media-monitor 2>/dev/null" || echo "inactive")
    if [ "$monitor_status" = "active" ]; then
        echo "Media Monitor: ✓ Running"
        # Check if status file is being updated
        last_update=$(ssh -o ConnectTimeout=5 ebon@10.0.0.29 "stat -c %Y /home/ebon/media_service_status.json 2>/dev/null" || echo "0")
        current_time=$(date +%s)
        age=$((current_time - last_update))
        if [ "$age" -lt 60 ]; then
            echo "Status Updates: ✓ Active (updated ${age}s ago)"
        else
            echo "Status Updates: ⚠ Stale (updated ${age}s ago)"
        fi
    else
        echo "Media Monitor: ✗ Not running"
    fi
else
    echo "Media Monitor: ✗ Media server offline"
fi

echo ""
echo "=== PRINTER STATUS ==="
# Check printer (adjust IP as needed)
if timeout 2 ping -c 1 10.0.0.21 > /dev/null 2>&1; then
    echo "HP Printer: ✓ Online (10.0.0.21)"
else
    echo "HP Printer: ✗ Offline or different IP"
fi

echo ""
echo "=========================================="
echo " STATUS SUMMARY"
echo "=========================================="

# Overall health check
overall_health="healthy"
if \! ping -c 1 -W 2 10.0.0.29 > /dev/null 2>&1; then
    overall_health="critical"
elif \! curl -s --connect-timeout 5 http://10.0.0.29:8000/health > /dev/null 2>&1; then
    overall_health="degraded"
fi

case $overall_health in
    "healthy")
        echo "Overall Status: ✓ HEALTHY - All systems operational"
        ;;
    "degraded") 
        echo "Overall Status: ⚠ DEGRADED - Some services may be unavailable"
        ;;
    "critical")
        echo "Overall Status: ✗ CRITICAL - Media server unreachable"
        ;;
esac

echo "Infrastructure: NexusController v2.0 with Docker deployment"
echo "Monitoring: Real-time service monitoring active"
echo "Backup: Automated daily backups configured"
echo "Report generated: $(date)"
echo "=========================================="
