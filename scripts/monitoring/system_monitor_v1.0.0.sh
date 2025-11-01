#!/bin/bash

# Ebon System Monitor Agent
# Monitors system health and sends alerts

LOG_FILE="/var/log/ebon_monitor.log"
ALERT_FILE="/home/ebon/monitor_alerts.log"
EMAIL="eboncorp@gmail.com"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local severity=$1
    local message=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] $message" >> "$ALERT_FILE"
    # Email alerts enabled:
    echo "$message" | mail -s "Ebon System Alert: $severity" "$EMAIL"
}

# Check disk usage
check_disk() {
    df -h | grep -v tmpfs | grep -v udev | awk 'NF>=6 && $5 ~ /%/ {print $5 " " $6}' | while read output; do
        usage=$(echo $output | awk '{print $1}' | sed 's/%//')
        partition=$(echo $output | awk '{print $2}')
        if [ -n "$usage" ] && [ "$usage" -eq "$usage" ] 2>/dev/null && [ "$usage" -ge 85 ]; then
            send_alert "WARNING" "Disk usage on $partition is at ${usage}%"
        fi
    done
}

# Check memory usage
check_memory() {
    mem_usage=$(free | grep Mem | awk '{printf "%d", $3/$2 * 100}')
    if [ -n "$mem_usage" ] && [ "$mem_usage" -ge 90 ]; then
        send_alert "WARNING" "Memory usage is at ${mem_usage}%"
    fi
}

# Check Docker containers
check_docker() {
    unhealthy=$(docker ps --filter health=unhealthy --format "{{.Names}}" 2>/dev/null)
    if [ -n "$unhealthy" ]; then
        send_alert "ERROR" "Unhealthy Docker containers: $unhealthy - attempting auto-recovery"
        /home/ebon/auto_recovery.sh &
    fi

    # Check if expected containers are running
    expected_containers=("jellyfin" "homeassistant-fixed" "nexuscontroller-media-fixed" "nodered" "mosquitto")
    for container in "${expected_containers[@]}"; do
        if ! docker ps --format "{{.Names}}" | grep -q "^$container$"; then
            send_alert "ERROR" "Container $container is not running - attempting auto-recovery"
            /home/ebon/auto_recovery.sh &
        fi
    done
}

# Check system load
check_load() {
    load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    cpu_cores=$(nproc)
    threshold=$(echo "$cpu_cores * 2" | bc)

    if (( $(echo "$load_1min > $threshold" | bc -l) )); then
        send_alert "WARNING" "High system load: $load_1min (threshold: $threshold)"
    fi
}

# Check backup status
check_backups() {
    # Check if last backup was successful
    if [ -f "/home/ebon/backup.log" ]; then
        last_backup=$(tail -1 /home/ebon/backup.log | grep "Complete")
        if [ -z "$last_backup" ]; then
            last_line=$(tail -1 /home/ebon/backup.log)
            if [[ "$last_line" == *"Error"* ]] || [[ "$last_line" == *"Failed"* ]]; then
                send_alert "ERROR" "Backup may have failed. Last log: $last_line"
            fi
        fi
    fi
}

# Check services
check_services() {
    critical_services=("docker" "ssh" "tailscaled")
    for service in "${critical_services[@]}"; do
        if ! systemctl is-active --quiet "$service"; then
            send_alert "ERROR" "Service $service is not running - attempting auto-recovery"
            # Trigger auto-recovery
            /home/ebon/auto_recovery.sh &
        fi
    done
}

# Check for failed systemd units
check_failed_units() {
    failed_output=$(systemctl list-units --failed --no-legend --no-pager)
    if [ -n "$failed_output" ]; then
        failed_list=$(echo "$failed_output" | awk '{print $2}' | tr '\n' ' ')
        send_alert "WARNING" "Failed systemd units: $failed_list"
    fi
}

# Check service connectivity
check_service_connectivity() {
    # Test NexusController health
    if ! curl -s -f "http://10.0.0.29:8000/health" >/dev/null 2>&1; then
        send_alert "WARNING" "NexusController API not responding"
    fi

    # Test Jellyfin health
    if ! curl -s -f "http://10.0.0.29:8096/health" >/dev/null 2>&1; then
        send_alert "WARNING" "Jellyfin service not responding"
    fi

    # Test HomeAssistant (accept 200 or 302)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.0.0.29:8123")
    if [[ "$http_code" != "200" && "$http_code" != "302" ]]; then
        send_alert "WARNING" "HomeAssistant service not responding (HTTP $http_code)"
    fi
}

# Main monitoring loop
log_message "System Monitor Started"

# Run all checks
check_disk
check_memory
check_docker
check_load
check_backups
check_services
check_failed_units
check_service_connectivity

# Summary
if [ ! -s "$ALERT_FILE" ] || [ "$(find "$ALERT_FILE" -mmin -5 | wc -l)" -eq 0 ]; then
    log_message "All systems operational"
else
    recent_alerts=$(find "$ALERT_FILE" -mmin -5 | wc -l)
    if [ "$recent_alerts" -gt 0 ]; then
        log_message "Found $recent_alerts recent alerts - check $ALERT_FILE"
    fi
fi