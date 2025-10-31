# Complete Home Cloud Setup Guide - Part 2

## Part 4: Automation and Media Management

### 4.1 Media Automation Stack

#### Basic Docker Compose Setup
```yaml
version: '3.8'

services:
  sonarr:
    image: linuxserver/sonarr:latest
    container_name: sonarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
    volumes:
      - /opt/docker/data/sonarr:/config
      - /tank/media/tv:/tv
      - /tank/downloads:/downloads
    ports:
      - 8989:8989
    restart: unless-stopped
    networks:
      - media_net

  radarr:
    image: linuxserver/radarr:latest
    container_name: radarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
    volumes:
      - /opt/docker/data/radarr:/config
      - /tank/media/movies:/movies
      - /tank/downloads:/downloads
    ports:
      - 7878:7878
    restart: unless-stopped
    networks:
      - media_net

  prowlarr:
    image: linuxserver/prowlarr:latest
    container_name: prowlarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
    volumes:
      - /opt/docker/data/prowlarr:/config
    ports:
      - 9696:9696
    restart: unless-stopped
    networks:
      - media_net

  bazarr:
    image: linuxserver/bazarr:latest
    container_name: bazarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
    volumes:
      - /opt/docker/data/bazarr:/config
      - /tank/media/movies:/movies
      - /tank/media/tv:/tv
    ports:
      - 6767:6767
    restart: unless-stopped
    networks:
      - media_net

networks:
  media_net:
    driver: bridge
```

#### Example Configurations

##### Sonarr Series Configuration
```json
{
  "series": {
    "title": "The Mandalorian",
    "path": "/tv/The Mandalorian",
    "qualityProfileId": 1,
    "seasonFolder": true,
    "monitored": true,
    "languageProfileId": 1,
    "tags": [
      1,
      2
    ],
    "addOptions": {
      "searchForMissingEpisodes": true,
      "searchForCutoffUnmetEpisodes": false
    }
  },
  "qualityProfile": {
    "name": "HD-1080p",
    "cutoff": 9,
    "items": [
      {
        "quality": {
          "id": 9,
          "name": "WEBRip-1080p"
        },
        "allowed": true
      },
      {
        "quality": {
          "id": 7,
          "name": "Bluray-1080p"
        },
        "allowed": true
      }
    ]
  }
}
```

##### Radarr Movie Configuration
```json
{
  "movie": {
    "title": "Dune",
    "year": 2021,
    "qualityProfileId": 1,
    "path": "/movies/Dune (2021)",
    "monitored": true,
    "minimumAvailability": "released",
    "tags": [
      1
    ],
    "addOptions": {
      "searchForMovie": true
    }
  },
  "qualityProfile": {
    "name": "4K HDR",
    "cutoff": 18,
    "items": [
      {
        "quality": {
          "id": 18,
          "name": "WEBRip-2160p"
        },
        "allowed": true
      },
      {
        "quality": {
          "id": 19,
          "name": "Bluray-2160p"
        },
        "allowed": true
      }
    ]
  }
}
```

### 4.2 Automation Scripts

#### Media Organization Script
```python
#!/usr/bin/env python3
import os
import shutil
import re
from datetime import datetime

def organize_media(source_dir, movies_dir, tv_dir):
    """
    Organizes media files into proper directories
    """
    # Movie pattern: Title (Year) [Quality].mkv
    movie_pattern = r"(.+?)\s*\((\d{4})\).*\.(mkv|mp4|avi)$"
    # TV pattern: Show.Name.S01E02.mkv
    tv_pattern = r"(.+?)[\.\s][Ss](\d{2})[Ee](\d{2}).*\.(mkv|mp4|avi)$"

    for filename in os.listdir(source_dir):
        filepath = os.path.join(source_dir, filename)
        
        # Check if it's a movie
        movie_match = re.match(movie_pattern, filename, re.IGNORECASE)
        if movie_match:
            title, year = movie_match.groups()[:2]
            movie_dir = os.path.join(movies_dir, f"{title} ({year})")
            os.makedirs(movie_dir, exist_ok=True)
            shutil.move(filepath, os.path.join(movie_dir, filename))
            continue

        # Check if it's a TV show
        tv_match = re.match(tv_pattern, filename, re.IGNORECASE)
        if tv_match:
            show, season, episode = tv_match.groups()[:3]
            show = show.replace('.', ' ')
            show_dir = os.path.join(tv_dir, show)
            season_dir = os.path.join(show_dir, f"Season {int(season):02d}")
            os.makedirs(season_dir, exist_ok=True)
            shutil.move(filepath, os.path.join(season_dir, filename))

# Usage example
organize_media(
    "/tank/downloads/complete",
    "/tank/media/movies",
    "/tank/media/tv"
)
```

#### Automated Backup Script
```bash
#!/bin/bash

# Configuration
SOURCE_DIR="/tank/media"
BACKUP_DIR="/backup"
LOG_FILE="/var/log/backup.log"
RETENTION_DAYS=30

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Create snapshot
create_snapshot() {
    SNAPSHOT_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    zfs snapshot "tank/media@${SNAPSHOT_NAME}"
    log_message "Created snapshot: ${SNAPSHOT_NAME}"
}

# Sync to backup location
sync_backup() {
    rsync -avz --delete \
        --exclude '*.partial~' \
        --exclude '*.part' \
        "${SOURCE_DIR}/" \
        "${BACKUP_DIR}/"
    
    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        log_message "Backup completed successfully"
    else
        log_message "Backup failed with error code: $RESULT"
    fi
}

# Clean old snapshots
clean_snapshots() {
    zfs list -H -t snapshot -o name,creation | while read SNAPSHOT CREATION; do
        SNAPSHOT_DATE=$(date -d "$CREATION" +%s)
        CURRENT_DATE=$(date +%s)
        DAYS_OLD=$(( ($CURRENT_DATE - $SNAPSHOT_DATE) / 86400 ))
        
        if [ $DAYS_OLD -gt $RETENTION_DAYS ]; then
            zfs destroy "$SNAPSHOT"
            log_message "Deleted old snapshot: $SNAPSHOT"
        fi
    done
}

# Main execution
log_message "Starting backup process"
create_snapshot
sync_backup
clean_snapshots
log_message "Backup process completed"
```

### 4.3 Media Processing

#### FFmpeg Transcoding Script
```bash
#!/bin/bash

# Configuration
INPUT_DIR="/tank/media/processing"
OUTPUT_DIR="/tank/media/encoded"
LOG_FILE="/var/log/encoding.log"

# Encoding profiles
declare -A PROFILES
PROFILES=(
    ["1080p"]="scale=-1:1080 -c:v libx264 -crf 22 -preset medium -c:a aac -b:a 192k"
    ["720p"]="scale=-1:720 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k"
    ["480p"]="scale=-1:480 -c:v libx264 -crf 24 -preset medium -c:a aac -b:a 96k"
)

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to process video
process_video() {
    local input_file="$1"
    local profile="$2"
    local profile_settings="${PROFILES[$profile]}"
    
    # Generate output filename
    filename=$(basename "$input_file")
    filename_no_ext="${filename%.*}"
    output_file="${OUTPUT_DIR}/${filename_no_ext}_${profile}.mp4"
    
    # Create output directory if it doesn't exist
    mkdir -p "$OUTPUT_DIR"
    
    # Process the video
    ffmpeg -i "$input_file" \
        -filter:v "$profile_settings" \
        -movflags +faststart \
        "$output_file" \
        2>> "$LOG_FILE"
    
    local result=$?
    if [ $result -eq 0 ]; then
        log_message "Successfully encoded: $filename to $profile"
    else
        log_message "Failed to encode: $filename to $profile"
    fi
    
    return $result
}

# Main processing loop
for input_file in "$INPUT_DIR"/*; do
    if [ -f "$input_file" ]; then
        log_message "Processing file: $input_file"
        
        # Process for each profile
        for profile in "${!PROFILES[@]}"; do
            process_video "$input_file" "$profile"
        done
    fi
done
```

### 4.4 Automation Schedule

#### Crontab Configuration
```bash
# Media organization (every 15 minutes)
*/15 * * * * /opt/scripts/organize_media.py

# Daily backup (at 2 AM)
0 2 * * * /opt/scripts/backup.sh

# Weekly media library scan (Sundays at 3 AM)
0 3 * * 0 curl http://localhost:32400/library/scan?X-Plex-Token=YOUR_TOKEN

# Monthly storage cleanup (1st of month at 4 AM)
0 4 1 * * /opt/scripts/storage_cleanup.sh

# Health check (every hour)
0 * * * * /opt/scripts/health_check.sh
```

#### Health Check Script
```bash
#!/bin/bash

# Configuration
SERVICES=("plex" "sonarr" "radarr" "prowlarr" "bazarr")
NOTIFICATION_EMAIL="admin@example.com"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-app-password"

# Function to check if a Docker container is running
check_container() {
    local container=$1
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        return 1
    fi
    return 0
}

# Function to check disk space
check_disk_space() {
    local threshold=90
    local usage=$(df -h | grep '/tank/media' | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -gt "$threshold" ]; then
        return 1
    fi
    return 0
}

# Function to send email notification
send_notification() {
    local subject="$1"
    local message="$2"
    
    echo "$message" | mail -s "$subject" \
        -S smtp="smtp://${SMTP_SERVER}:${SMTP_PORT}" \
        -S smtp-use-starttls \
        -S smtp-auth=login \
        -S smtp-auth-user="${SMTP_USER}" \
        -S smtp-auth-password="${SMTP_PASS}" \
        "${NOTIFICATION_EMAIL}"
}

# Main checks
issues=()

# Check services
for service in "${SERVICES[@]}"; do
    if ! check_container "$service"; then
        issues+=("Container $service is not running")
    fi
done

# Check disk space
if ! check_disk_space; then
    issues+=("Disk space usage is above threshold")
fi

# Send notification if there are issues
if [ ${#issues[@]} -gt 0 ]; then
    message="The following issues were detected:\n\n"
    for issue in "${issues[@]}"; do
        message+="- $issue\n"
    done
    send_notification "Media Server Alert" "$message"
fi
```

I'll continue with the security configuration, remote access setup, and remaining sections. Would you like me to proceed?