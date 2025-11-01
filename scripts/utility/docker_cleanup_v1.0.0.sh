#!/bin/bash

# Docker Cleanup Script
# Removes unused Docker resources to free up space

LOG_FILE="/var/log/docker_cleanup.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "Starting Docker cleanup..."

# Remove stopped containers older than 24 hours
log_message "Removing stopped containers..."
docker container prune -f --filter "until=24h" >> "$LOG_FILE" 2>&1

# Remove unused images
log_message "Removing unused images..."
docker image prune -f -a --filter "until=72h" >> "$LOG_FILE" 2>&1

# Remove unused volumes
log_message "Removing unused volumes..."
docker volume prune -f >> "$LOG_FILE" 2>&1

# Remove unused networks
log_message "Removing unused networks..."
docker network prune -f >> "$LOG_FILE" 2>&1

# Show disk usage after cleanup
AFTER_SIZE=$(docker system df --format "table {{.Type}}\t{{.Size}}" | grep -E "Images|Containers|Volumes" | awk '{sum+=$2} END {print sum}')
log_message "Cleanup complete. Docker is now using: ${AFTER_SIZE:-unknown} space"

# Clean build cache older than 7 days
log_message "Cleaning build cache..."
docker builder prune -f --filter "until=168h" >> "$LOG_FILE" 2>&1

log_message "Docker cleanup finished"