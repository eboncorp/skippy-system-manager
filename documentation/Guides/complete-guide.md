# Complete Home Cloud Setup Guide

## Part 1: Planning and Hardware Selection

### 1.1 Budget Planning
```plaintext
Entry Level ($1,000-1,500):
- Synology DS220+ ($300)
- 2x 8TB WD Red Plus ($360)
- UPS ($150)
- Network Equipment ($200)

Mid-Range ($2,000-2,500):
- Synology DS920+ ($550)
- 4x 8TB WD Red Plus ($720)
- UPS ($200)
- Network Equipment ($400)

High-End ($3,500+):
- Custom Build or Synology DS1621+ ($900)
- 6x 14TB WD Red Pro ($1,800)
- UPS ($300)
- Network Equipment ($600)
```

### 1.2 Custom Server Build Specification
```plaintext
Base System ($1,500):
CPU: Intel i5-12400 ($200)
  - 6 cores/12 threads
  - QuickSync for transcoding
  - Excellent power efficiency

Motherboard: ASUS TUF Gaming B660M-PLUS ($180)
  - 6x SATA ports
  - 2x M.2 slots
  - 2.5GbE LAN

RAM: 32GB DDR4-3200 ($120)
  - 2x16GB configuration
  - ECC if supported

Case: Fractal Design Define 7 ($200)
  - 14+ drive bays
  - Excellent airflow
  - Sound dampening

PSU: Seasonic FOCUS 750W Gold ($120)
  - Highly reliable
  - Efficient under low load
  - Semi-passive cooling

Boot Drive: Samsung 970 EVO Plus 500GB ($70)
  - OS and Docker containers
  - Fast boot times
  - Reliable operation

OS Drive: Samsung 870 EVO 1TB ($100)
  - Application data
  - Cache
  - Temporary transcoding

Cooling:
- Noctua NH-U12S ($70)
- 4x Noctua NF-A14 PWM ($100)

Additional:
- LSI HBA Card ($100) if more SATA ports needed
- 10GbE card ($100) for future expansion
```

### 1.3 Storage Configuration

#### RAID Planning
```plaintext
2-Bay Setup:
- RAID 1: 1:1 mirroring
- Pros: Simple, good redundancy
- Cons: 50% capacity loss

4-Bay Setup:
- RAID 5: Single parity
- Usable space: n-1 drives
- Good balance of space/safety

6-Bay Setup:
- RAID 6: Dual parity
- Usable space: n-2 drives
- Best for large arrays

Alternative: UnRAID
- Mix different drive sizes
- Data protection with parity
- Easy expansion
- Cache pools
```

#### Drive Selection Guide
```plaintext
NAS Drives Comparison:

WD Red Plus:
- CMR technology
- 180TB/year workload
- 5-year warranty
- Best value option

Seagate IronWolf:
- Higher workload rating
- Built-in health monitoring
- Slightly louder
- Competitive pricing

WD Red Pro:
- 300TB/year workload
- 7200 RPM
- Better performance
- Higher cost

Recommended Configurations:

Entry Level:
- 2x 8TB WD Red Plus
- RAID 1
- 8TB usable

Mid-Range:
- 4x 8TB WD Red Plus
- RAID 5
- 24TB usable

High-End:
- 6x 14TB WD Red Pro
- RAID 6
- 56TB usable
```

## Part 2: Network Infrastructure

### 2.1 Network Hardware

#### Router Selection
```plaintext
Recommended Models:

1. ASUS RT-AX86U ($250)
- Excellent QoS
- Strong CPU
- Good VPN support
- Merlin firmware compatible

2. Ubiquiti Dream Machine Pro ($379)
- Enterprise features
- Built-in protect
- Network segmentation
- 10GbE support

3. OPNsense/pfSense Build ($300)
- Protectli Vault FB6
- Complete control
- Advanced features
- Best performance
```

#### Network Switch
```plaintext
Entry Level:
- TP-Link TL-SG108E ($30)
- 8 ports
- Basic VLAN
- Link aggregation

Mid-Range:
- NETGEAR GS308T ($90)
- 8 ports
- Advanced VLAN
- IGMP snooping

High-End:
- Ubiquiti USW-24-POE ($699)
- 24 ports
- POE support
- 10GbE uplinks
```

### 2.2 Network Configuration

#### VLAN Setup
```plaintext
VLAN 10 - Management (10.0.10.0/24):
- NAS
- Router
- Switches
- Security cameras

VLAN 20 - Media (10.0.20.0/24):
- Plex clients
- Smart TVs
- Streaming devices
- Game consoles

VLAN 30 - Personal (10.0.30.0/24):
- Computers
- Phones
- Tablets
- Work devices

VLAN 40 - IoT (10.0.40.0/24):
- Smart home devices
- Voice assistants
- IoT sensors
```

#### QoS Configuration
```plaintext
High Priority:
- VoIP
- Remote desktop
- Gaming
- Video calls

Medium Priority:
- Web browsing
- Streaming
- Downloads
- Social media

Low Priority:
- Updates
- Backups
- P2P
- Background tasks

Bandwidth Allocation:
- High: 60% guaranteed
- Medium: 30% guaranteed
- Low: 10% guaranteed
- Unused bandwidth flows down
```

## Part 3: Software Installation and Configuration

### 3.1 Operating System Setup

#### TrueNAS Scale Installation
```bash
# 1. Download TrueNAS Scale ISO
# 2. Create bootable USB
# 3. Boot and install
# 4. Initial configuration

# Network setup
Interface: em0
IPv4: 10.0.10.10
Mask: 255.255.255.0
Gateway: 10.0.10.1
DNS: 10.0.10.1

# Storage setup
1. Create pool:
   - Name: tank
   - RAID-Z2 (6 drives)
   
2. Create datasets:
   - tank/media
   - tank/backups
   - tank/docker
   - tank/personal

3. Set permissions:
   - Owner: media
   - Group: media
   - Permissions: 755
```

#### UnRAID Alternative Setup
```plaintext
1. USB Flash Drive:
   - Format with FAT32
   - Copy UnRAID files
   - Set boot order

2. Array Configuration:
   - Parity drive: Largest drive
   - Data drives: Additional drives
   - Cache: SSD pool

3. Share Setup:
   - Movies: /mnt/user/media/movies
   - TV: /mnt/user/media/tv
   - Music: /mnt/user/media/music
   - Personal: /mnt/user/personal

4. Docker Setup:
   - Default path: /mnt/user/appdata/
   - Download path: /mnt/user/downloads/
```

### 3.2 Docker Infrastructure

#### Docker Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.9.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create directory structure
mkdir -p /opt/docker/{configs,data,compose}
```

#### Base Docker Compose
```yaml
version: '3.8'

networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
  backend:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/24

services:
  traefik:
    image: traefik:latest
    container_name: traefik
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/docker/configs/traefik:/etc/traefik
    networks:
      - frontend
      - backend
    labels:
      - "traefik.enable=true"

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --schedule "0 0 4 * * *" --cleanup
    restart: unless-stopped
```

### 3.3 Media Server Setup

#### Plex Installation
```yaml
version: '3.8'

services:
  plex:
    image: plexinc/pms-docker
    container_name: plex
    network_mode: host
    environment:
      - PLEX_CLAIM=claim-xxxxx
      - ADVERTISE_IP=http://10.0.10.10:32400
    volumes:
      - /opt/docker/data/plex:/config
      - /tank/media:/data
    devices:
      - /dev/dri:/dev/dri # For hardware transcoding
    restart: unless-stopped
```

#### Media Organization
```plaintext
/tank/media/
├── movies/
│   ├── Movie (Year)/
│   │   ├── Movie (Year).mkv
│   │   ├── Movie (Year).en.srt
│   │   └── poster.jpg
├── tv/
│   ├── Show Name/
│   │   ├── Season 01/
│   │   │   ├── Show Name - S01E01.mkv
│   │   │   └── Show Name - S01E02.mkv
├── music/
│   ├── Artist/
│   │   ├── Album/
│   │   │   ├── 01 - Track.flac
│   │   │   └── cover.jpg
```

I'll continue with the remaining sections covering automation, security, maintenance, mobile access, and optimization in the next part. Would you like me to proceed?