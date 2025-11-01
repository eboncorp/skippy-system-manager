#!/bin/bash

# Emergency Recovery Script
# Run this manually when system is in bad state

echo "🚨 EMERGENCY RECOVERY MODE 🚨"
echo "==============================="

LOG_FILE="/var/log/emergency_recovery.log"

log_and_print() {
    echo "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_and_print "Emergency recovery started"

# 1. Check system resources
echo ""
echo "📊 System Resources:"
df -h | grep -E "^/dev"
free -h
uptime

# 2. Restart all critical services
echo ""
echo "🔄 Restarting critical services..."
critical_services=("docker" "ssh" "tailscaled")
for service in "${critical_services[@]}"; do
    echo -n "  $service: "
    if sudo systemctl restart "$service"; then
        echo "✅"
        log_and_print "Restarted $service successfully"
    else
        echo "❌"
        log_and_print "Failed to restart $service"
    fi
done

# 3. Restart all Docker containers
echo ""
echo "🐳 Restarting Docker containers..."
docker ps -a --format "{{.Names}}" | while read container; do
    if [ -n "$container" ]; then
        echo -n "  $container: "
        if docker restart "$container" >/dev/null 2>&1; then
            echo "✅"
            log_and_print "Restarted container $container successfully"
        else
            echo "❌"
            log_and_print "Failed to restart container $container"
        fi
    fi
done

# 4. Clean up disk space if needed
echo ""
echo "🧹 Cleaning up disk space..."
df_output=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$df_output" -gt 85 ]; then
    echo "  High disk usage detected ($df_output%), performing cleanup..."

    # Docker cleanup
    docker system prune -f >/dev/null 2>&1
    echo "  ✅ Docker cleanup completed"

    # Log cleanup
    sudo find /var/log -name "*.log" -mtime +7 -delete 2>/dev/null
    echo "  ✅ Old logs cleaned"

    # Temp cleanup
    sudo find /tmp -type f -mtime +1 -delete 2>/dev/null
    echo "  ✅ Temp files cleaned"

    log_and_print "Emergency disk cleanup completed"
else
    echo "  Disk usage OK ($df_output%)"
fi

# 5. Check final status
echo ""
echo "📋 Final Status Check:"
echo "  Services:"
for service in docker ssh tailscaled; do
    if systemctl is-active --quiet "$service"; then
        echo "    $service: ✅ Running"
    else
        echo "    $service: ❌ Not running"
    fi
done

echo "  Containers:"
for container in jellyfin homeassistant-fixed nexuscontroller-media-fixed nodered mosquitto; do
    if docker ps --format "{{.Names}}" | grep -q "^$container$"; then
        echo "    $container: ✅ Running"
    else
        echo "    $container: ❌ Not running"
    fi
done

echo ""
echo "✅ Emergency recovery completed!"
echo "Check /var/log/emergency_recovery.log for details"

log_and_print "Emergency recovery completed"