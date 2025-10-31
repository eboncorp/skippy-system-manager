# Personal Cloud Software Stack Configuration

## Core Services

### 1. Media Server (Plex)

#### Installation
```bash
# On Synology
- Package Center → Install Plex Media Server
# On Custom Server (Ubuntu)
wget https://downloads.plex.tv/plex-media-server-new/[version]/debian/plexmediaserver_[version]_amd64.deb
sudo dpkg -i plexmediaserver_[version]_amd64.deb
```

#### Configuration
```yaml
# Media Folders Structure
/volume1/media/
  ├── movies/
  │   ├── Movie (Year)/
  │   │   ├── Movie (Year).mkv
  │   │   └── subtitles/
  ├── tv/
  │   ├── Show Name/
  │   │   ├── Season 01/
  │   │   │   ├── Show Name - S01E01.mkv
  ├── music/
  │   ├── Artist/
  │   │   ├── Album/
  │   │   │   ├── 01 - Track.mp3
```

#### Plex Settings
```yaml
# Transcoding Settings
Hardware Acceleration: Enabled (Intel QuickSync)
Transcoder Quality: Automatic
Background Transcoding x264 Preset: Medium
Maximum simultaneous transcode: 4

# Library Settings
Scanner: Plex Movie/Plex TV Series
Agent: New Plex Movie/TV Agent
Enable video preview thumbnails: Yes
Enable intro detection: Yes
```

### 2. Cloud Storage (NextCloud)

#### Installation (Docker)
```yaml
version: '3'
services:
  nextcloud:
    image: nextcloud
    ports:
      - 8080:80
    volumes:
      - nextcloud:/var/www/html
      - /volume1/nextcloud/data:/var/www/html/data
    environment:
      - MYSQL_HOST=db
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=secure_password
    depends_on:
      - db

  db:
    image: mariadb
    volumes:
      - db:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=secure_root_password
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=secure_password

volumes:
  nextcloud:
  db:
```

#### NextCloud Apps to Install
- Files
- Calendar
- Contacts
- Photos
- Tasks
- Notes
- Collaborative editing
- Two-factor authentication

### 3. Automated Media Management

#### Sonarr (TV Shows)
```yaml
# Docker Configuration
version: '3'
services:
  sonarr:
    image: linuxserver/sonarr
    ports:
      - 8989:8989
    volumes:
      - /volume1/docker/sonarr:/config
      - /volume1/media/tv:/tv
      - /volume1/downloads:/downloads
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Your/Timezone
```

#### Radarr (Movies)
```yaml
# Docker Configuration
version: '3'
services:
  radarr:
    image: linuxserver/radarr
    ports:
      - 7878:7878
    volumes:
      - /volume1/docker/radarr:/config
      - /volume1/media/movies:/movies
      - /volume1/downloads:/downloads
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Your/Timezone
```

## Security Services

### 1. Reverse Proxy (Nginx Proxy Manager)
```yaml
version: '3'
services:
  npm:
    image: jc21/nginx-proxy-manager
    ports:
      - 80:80
      - 443:443
      - 81:81
    volumes:
      - /volume1/docker/npm/data:/data
      - /volume1/docker/npm/letsencrypt:/etc/letsencrypt
```

### 2. VPN Server (WireGuard)
```yaml
version: '3'
services:
  wireguard:
    image: linuxserver/wireguard
    ports:
      - 51820:51820/udp
    volumes:
      - /volume1/docker/wireguard:/config
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Your/Timezone
      - SERVERURL=your.domain.com
      - SERVERPORT=51820
      - PEERS=3
```

## Monitoring Stack

### 1. System Monitoring (Prometheus + Grafana)
```yaml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - 9090:9090
    volumes:
      - /volume1/docker/prometheus:/etc/prometheus
      
  grafana:
    image: grafana/grafana
    ports:
      - 3000:3000
    volumes:
      - /volume1/docker/grafana:/var/lib/grafana
```

### 2. Log Management (Graylog)
```yaml
version: '3'
services:
  graylog:
    image: graylog/graylog
    ports:
      - 9000:9000
      - 12201:12201/udp
    volumes:
      - /volume1/docker/graylog/data:/usr/share/graylog/data
    environment:
      - GRAYLOG_PASSWORD_SECRET=somepasswordpepper
      - GRAYLOG_ROOT_PASSWORD_SHA2=8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
```

## Backup Configuration

### 1. Data Backup (Duplicati)
```yaml
version: '3'
services:
  duplicati:
    image: linuxserver/duplicati
    ports:
      - 8200:8200
    volumes:
      - /volume1/docker/duplicati:/config
      - /volume1/media:/source/media
      - /volume1/nextcloud:/source/nextcloud
      - /backup:/backup
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Your/Timezone
```

### 2. Docker Backup Script
```bash
#!/bin/bash
# Backup Docker volumes and configurations

BACKUP_DIR="/volume1/backup/docker"
DATE=$(date +%Y%m%d)

# Stop containers
docker-compose down

# Backup volumes
tar -czf $BACKUP_DIR/volumes_$DATE.tar.gz /volume1/docker

# Backup docker-compose files
tar -czf $BACKUP_DIR/compose_$DATE.tar.gz /volume1/docker-compose

# Restart containers
docker-compose up -d
```
