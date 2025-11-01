#!/bin/bash

# Music Organization Supervisor
# Ensures the music organizer keeps running until completion

LOG_FILE="/home/ebon/music_org_supervisor.log"
ORGANIZER_SCRIPT="/home/ebon/robust_music_organizer.py"
STATE_FILE="/home/ebon/music_org_state.json"
PID_FILE="/home/ebon/music_org.pid"
CHECK_INTERVAL=30

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_completion() {
    # Check if all files have been processed
    if [ -f "/home/ebon/music_org_summary.json" ]; then
        if grep -q '"errors": 0' "/home/ebon/music_org_summary.json" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

start_organizer() {
    log_message "Starting music organizer..."
    nohup python3 "$ORGANIZER_SCRIPT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    log_message "Organizer started with PID $(cat $PID_FILE)"
}

log_message "Music Organization Supervisor starting..."

# Main supervision loop
while true; do
    if check_completion; then
        log_message "Organization completed successfully!"
        break
    fi
    
    if ! is_running; then
        log_message "Organizer not running, restarting..."
        start_organizer
        sleep 5
    else
        # Get progress stats
        if [ -f "$STATE_FILE" ]; then
            PROCESSED=$(grep -o '"processed_count": [0-9]*' "$STATE_FILE" | grep -o '[0-9]*')
            log_message "Organizer running. Files processed: $PROCESSED"
        fi
    fi
    
    sleep "$CHECK_INTERVAL"
done

log_message "Supervisor exiting - organization complete"
