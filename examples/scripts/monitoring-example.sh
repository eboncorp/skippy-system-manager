#!/bin/bash
# Example: System Monitoring
# Demonstrates system monitoring with Skippy

set -euo pipefail

# Load configuration
source ../../config.env

# Generate system dashboard
echo "Generating system dashboard..."
bash ../../scripts/monitoring/system_dashboard_v1.0.0.sh snapshot

# Check specific metrics
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "${DISK_USAGE}" -gt 90 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
    # Send alert here
fi

echo "Monitoring complete"
