#!/bin/bash

# NexusController Status Report
echo "🔧 NexusController Status Report"
echo "================================"
echo ""

# Container status
echo "📦 Container Status:"
docker ps --filter name=nexus --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "💚 Health Check:"
curl -s http://10.0.0.29:8000/health | python3 -m json.tool 2>/dev/null || echo "Health endpoint not responding"

echo ""
echo "🌐 Available Endpoints:"
echo "  • Health Check: http://10.0.0.29:8000/health"
echo "  • API Documentation: http://10.0.0.29:8000/docs"
echo "  • Interactive API: http://10.0.0.29:8000/redoc"

echo ""
echo "📊 Monitored Services Status:"
curl -s http://10.0.0.29:8000/health | grep -o '"[^"]*":"[^"]*"' | while read line; do
    service=$(echo $line | cut -d'"' -f2)
    status=$(echo $line | cut -d'"' -f4)
    if [[ "$service" != "status" && "$service" != "timestamp" ]]; then
        if [[ "$status" == "running" ]]; then
            echo "  ✅ $service: $status"
        else
            echo "  ❌ $service: $status"
        fi
    fi
done

echo ""
echo "🔍 Recent Container Logs:"
docker logs nexuscontroller-media-fixed --tail 5

echo ""
echo "📈 Resource Usage:"
docker stats nexuscontroller-media-fixed --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "🛠️ Quick Actions:"
echo "  • Restart: docker restart nexuscontroller-media-fixed"
echo "  • View logs: docker logs nexuscontroller-media-fixed -f"
echo "  • Check health: curl http://10.0.0.29:8000/health"