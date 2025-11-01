#!/bin/bash

# Auto-Recovery Script
# Automatically attempts to fix common issues

LOG_FILE="/var/log/ebon_monitor.log"
ALERT_FILE="/home/ebon/monitor_alerts.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RECOVERY] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local severity=$1
    local message=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] $message" >> "$ALERT_FILE"
}

# Auto-restart critical services
restart_service() {
    local service=$1
    log_message "Attempting to restart $service"

    if sudo systemctl restart "$service"; then
        log_message "✅ Successfully restarted $service"
        send_alert "INFO" "Auto-recovered service: $service"
        return 0
    else
        log_message "❌ Failed to restart $service"
        send_alert "ERROR" "Failed to auto-recover service: $service - manual intervention required"
        return 1
    fi
}

# Auto-restart Docker containers
restart_container() {
    local container=$1
    log_message "Attempting to restart container $container"

    if docker restart "$container" >/dev/null 2>&1; then
        log_message "✅ Successfully restarted container $container"
        send_alert "INFO" "Auto-recovered container: $container"
        return 0
    else
        log_message "❌ Failed to restart container $container"
        send_alert "ERROR" "Failed to auto-recover container: $container - manual intervention required"
        return 1
    fi
}

# Check and fix disk space issues
cleanup_disk_space() {
    log_message "Performing emergency disk cleanup"

    # Clean Docker
    docker system prune -f >/dev/null 2>&1

    # Clean apt cache
    sudo apt clean >/dev/null 2>&1

    # Clean logs older than 7 days
    sudo find /var/log -type f -name "*.log" -mtime +7 -delete 2>/dev/null

    # Clean temp files
    sudo find /tmp -type f -mtime +1 -delete 2>/dev/null

    log_message "Emergency disk cleanup completed"
    send_alert "INFO" "Performed emergency disk cleanup"
}

# Main recovery logic
log_message "Auto-recovery agent started"

# Check for failed services and attempt restart
critical_services=("docker" "ssh" "tailscaled")
for service in "${critical_services[@]}"; do
    if ! systemctl is-active --quiet "$service"; then
        restart_service "$service"
    fi
done

# Check for unhealthy Docker containers
expected_containers=("jellyfin" "homeassistant-fixed" "nexuscontroller-media-fixed" "nodered" "mosquitto")
for container in "${expected_containers[@]}"; do
    if ! docker ps --format "{{.Names}}" | grep -q "^$container$"; then
        restart_container "$container"
    elif [ "$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)" = "unhealthy" ]; then
        restart_container "$container"
    fi
done

# Check disk usage and cleanup if critical
df -h | awk 'NR>1 {gsub(/%/, "", $5); if ($5 > 95) print $6}' | while read partition; do
    if [ -n "$partition" ]; then
        log_message "Critical disk usage detected on $partition"
        cleanup_disk_space
        break
    fi
done

log_message "Auto-recovery agent finished"