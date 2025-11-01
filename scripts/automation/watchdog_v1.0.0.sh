#!/bin/bash

# Watchdog service - monitors and auto-restarts critical components
# Runs more frequently than the system monitor for faster recovery

LOG_FILE="/var/log/watchdog.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Quick health check and restart if needed
quick_service_check() {
    local service=$1
    if ! systemctl is-active --quiet "$service"; then
        log_message "CRITICAL: $service down - auto-restarting"
        if sudo systemctl restart "$service"; then
            log_message "SUCCESS: $service restarted"
        else
            log_message "FAILED: Could not restart $service"
        fi
    fi
}

# Quick container check
quick_container_check() {
    local container=$1
    if ! docker ps --format "{{.Names}}" | grep -q "^$container$"; then
        log_message "CRITICAL: Container $container down - auto-restarting"
        if docker start "$container" >/dev/null 2>&1; then
            log_message "SUCCESS: Container $container restarted"
        else
            log_message "FAILED: Could not restart container $container"
        fi
    fi
}

# Critical services to monitor
critical_services=("docker" "ssh")
for service in "${critical_services[@]}"; do
    quick_service_check "$service"
done

# Critical containers to monitor
critical_containers=("jellyfin" "homeassistant-fixed")
for container in "${critical_containers[@]}"; do
    quick_container_check "$container"
done

# Keep log file from growing too large
if [ -f "$LOG_FILE" ] && [ $(wc -l < "$LOG_FILE") -gt 1000 ]; then
    tail -500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi