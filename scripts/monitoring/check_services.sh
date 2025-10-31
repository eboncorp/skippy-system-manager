#\!/bin/bash
# Service health check with alerts

CRITICAL_SERVICES=("docker" "ssh")
MEDIA_SERVER="10.0.0.29"

for service in "${CRITICAL_SERVICES[@]}"; do
    if \! systemctl is-active --quiet "$service"; then
        echo "ALERT: $service is down on $(hostname)" | logger -t nexus-monitor
    fi
done

# Check media server connectivity
if \! ping -c 1 -W 2 "$MEDIA_SERVER" > /dev/null 2>&1; then
    echo "ALERT: Media server $MEDIA_SERVER unreachable" | logger -t nexus-monitor
fi
