#!/bin/bash
# Service Control Script for Intelligent File Processor
# Manages the systemd service with API key configured

case "$1" in
    start)
        echo "Starting Intelligent File Processor service..."
        sudo systemctl start intelligent-file-processor.service
        sleep 2
        sudo systemctl status intelligent-file-processor.service
        ;;
    stop)
        echo "Stopping Intelligent File Processor service..."
        sudo systemctl stop intelligent-file-processor.service
        sudo systemctl status intelligent-file-processor.service
        ;;
    restart)
        echo "Restarting Intelligent File Processor service..."
        sudo systemctl restart intelligent-file-processor.service
        sleep 2
        sudo systemctl status intelligent-file-processor.service
        ;;
    status)
        sudo systemctl status intelligent-file-processor.service
        ;;
    logs)
        echo "Recent logs (last 50 lines):"
        sudo journalctl -u intelligent-file-processor.service -n 50 --no-pager
        ;;
    follow)
        echo "Following logs (Ctrl+C to exit):"
        sudo journalctl -u intelligent-file-processor.service -f
        ;;
    test-api)
        echo "Testing API key configuration..."
        sudo systemctl start intelligent-file-processor.service
        sleep 3
        if sudo journalctl -u intelligent-file-processor.service -n 20 | grep -q "Claude AI classification is available"; then
            echo "✅ API key is working - Claude AI available"
        elif sudo journalctl -u intelligent-file-processor.service -n 20 | grep -q "ANTHROPIC_API_KEY not set"; then
            echo "❌ API key not found in service environment"
        else
            echo "⚠️  Check logs with: ./SERVICE_CONTROL.sh logs"
        fi
        sudo systemctl stop intelligent-file-processor.service
        ;;
    *)
        echo "Intelligent File Processor Service Control"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|follow|test-api}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the processor daemon"
        echo "  stop      - Stop the processor daemon"
        echo "  restart   - Restart the processor daemon"
        echo "  status    - Show service status"
        echo "  logs      - Show recent logs"
        echo "  follow    - Follow logs in real-time"
        echo "  test-api  - Test if API key is configured correctly"
        echo ""
        echo "Note: API key is configured in systemd service file"
        echo "      No need to set ANTHROPIC_API_KEY in environment"
        exit 1
        ;;
esac
