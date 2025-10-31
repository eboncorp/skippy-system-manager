#\!/bin/bash
# NexusController Infrastructure Status

echo "=== NexusController Infrastructure Status ==="
echo "Generated: $(date)"
echo ""

# Main server status
echo "=== Main Server (10.0.0.1) ==="
echo "NexusController API: $(curl -s http://localhost:8000/health 2>/dev/null | grep -q "healthy" && echo "✓ Healthy" || echo "✗ Down")"
echo ""

# Media server status  
echo "=== Media Server (10.0.0.29) ==="
status=$(curl -s http://10.0.0.29:8000/api/v1/status 2>/dev/null)
if [ \! -z "$status" ]; then
    echo "NexusController API: ✓ Healthy"
    echo "Services Running: $(echo $status | python3 -c "import sys, json; print(json.load(sys.stdin)['services_running'])")/$(echo $status | python3 -c "import sys, json; print(json.load(sys.stdin)['services_total'])")"
    echo "Overall Status: $(echo $status | python3 -c "import sys, json; print(json.load(sys.stdin)['overall_status'])")"
    
    # List services
    echo ""
    echo "Media Services:"
    curl -s http://10.0.0.29:8000/api/v1/services 2>/dev/null | python3 -c "
import sys, json
services = json.load(sys.stdin)
for s in services:
    status_icon = '✓' if s['status'] == 'running' else '✗'
    health = f\" ({s['health']})\" if s.get('health') and s['health'] \!= 'unknown' else ''
    ports = f\" - Ports: {', '.join(set(p.split(':')[1] for p in s.get('ports', [])))}\" if s.get('ports') else ''
    print(f\"  {status_icon} {s['name']}: {s['status']}{health} - {s.get('uptime', 'unknown')}{ports}\")
"
else
    echo "NexusController API: ✗ Down"
fi

echo ""
echo "=== Network Services ==="
# Check key services
services=("10.0.0.29:8096:Jellyfin" "10.0.0.29:8123:Home-Assistant" "10.0.0.29:1883:MQTT" "10.0.0.29:1880:Node-RED")
for service in "${services[@]}"; do
    IFS=':' read -r host port name <<< "$service"
    nc -z -w1 $host $port 2>/dev/null && echo "  ✓ $name ($host:$port)" || echo "  ✗ $name ($host:$port)"
done

echo ""
echo "=== Printer Status ==="
# Check printer (if on network)
ping -c 1 -W 1 10.0.0.21 > /dev/null 2>&1 && echo "  ✓ HP Printer (10.0.0.21) - Online" || echo "  ✗ HP Printer - Offline or different IP"
