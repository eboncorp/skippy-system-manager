# Personal Home Cloud Network Setup Guide

## Overview
This guide will help you set up a personal cloud network for media streaming and large-scale storage, accessible both at home and remotely.

## Hardware Requirements

### Storage Server (NAS)
- **Recommended Options:**
  - Synology DiskStation (DS220+ or DS920+ for more drives)
  - QNAP NAS
  - Custom-built server with unRAID/TrueNAS
- **Hard Drives:**
  - Minimum 2 drives for redundancy
  - WD Red or Seagate IronWolf NAS drives
  - Recommended size: 4TB-14TB per drive

### Network Requirements
- **Router:**
  - Modern router with Gigabit ports
  - Support for UPnP/Port forwarding
- **Network Connection:**
  - Minimum 100Mbps upload speed for smooth remote streaming
  - Gigabit ethernet cables (Cat 6 or better)
- **Optional:**
  - Managed switch for network segmentation
  - Mesh WiFi system for better coverage

## Software Components

### Media Server Software
1. **Plex Media Server**
   - Industry standard for media streaming
   - Excellent device support
   - Automatic metadata fetching
   - transcoding capabilities

2. **Alternatives:**
   - Emby
   - Jellyfin (Open source)

### Cloud Storage Solutions
1. **NextCloud**
   - Self-hosted cloud storage
   - File sync across devices
   - Calendar and contacts sync
   - Collaborative tools

2. **Alternative:**
   - OwnCloud
   - Seafile

## Setup Instructions

### 1. NAS Setup
1. Install hard drives in NAS
2. Configure RAID (Recommended: RAID 1 for 2 drives, RAID 5 for 3+ drives)
3. Create shared folders:
   - Media (movies, TV shows, music)
   - Personal files
   - Backups

### 2. Media Server Setup
1. Install Plex Media Server on NAS
2. Configure libraries:
   ```
   Movies: /volume1/media/movies
   TV Shows: /volume1/media/tv
   Music: /volume1/media/music
   ```
3. Enable remote access in Plex settings
4. Configure transcoding settings based on your NAS capabilities

### 3. Remote Access Setup
1. **Dynamic DNS Setup:**
   - Create account with service (DuckDNS, No-IP)
   - Configure DDNS in router or NAS
   - Example hostname: yourdomain.duckdns.org

2. **Port Forwarding:**
   - Plex: TCP 32400
   - NextCloud: TCP 443 (HTTPS)
   - SSH (optional): TCP 22

3. **Security Measures:**
   - Enable HTTPS
   - Use strong passwords
   - Enable 2FA where possible
   - Regular security updates

### 4. Mobile Access Setup
1. Install apps:
   - Plex app
   - NextCloud app
   - VPN client (optional)

2. Configure apps:
   - Sign in with Plex account
   - Connect NextCloud using your DDNS address

## Best Practices

### Backup Strategy
1. **3-2-1 Backup Rule:**
   - 3 copies of data
   - 2 different media types
   - 1 offsite backup

2. **Automated Backups:**
   - Regular snapshots
   - Cloud backup for critical data
   - Test restore procedures

### Maintenance
1. **Regular Tasks:**
   - Check drive health monthly
   - Update software weekly
   - Verify backup integrity quarterly

2. **Monitoring:**
   - Set up email alerts for:
     - Drive failures
     - System updates
     - Backup failures

### Network Optimization
1. **Quality of Service (QoS):**
   - Prioritize streaming traffic
   - Set bandwidth limits for backups

2. **Network Segregation:**
   - Create separate VLAN for media devices
   - Use guest network for visitors

## Troubleshooting

### Common Issues
1. **Streaming Problems:**
   - Check network bandwidth
   - Verify transcoding settings
   - Test direct play vs transcoding

2. **Remote Access Issues:**
   - Verify port forwarding
   - Check DDNS status
   - Confirm ISP isn't blocking ports

### Performance Optimization
1. **Media Organization:**
   - Use consistent naming conventions
   - Organize content in proper folder structure
   - Keep media metadata updated

2. **Hardware Optimization:**
   - Monitor CPU/RAM usage
   - Configure cache settings
   - Adjust transcoding quality

## Expansion Options

### Future Upgrades
1. **Storage:**
   - Add more drives
   - Upgrade to larger capacity
   - Implement SSD cache

2. **Network:**
   - 10Gbe networking
   - Better WiFi coverage
   - UPS for power protection

### Additional Services
1. **Media Management:**
   - Sonarr (TV shows)
   - Radarr (movies)
   - Lidarr (music)

2. **Network Services:**
   - Pi-hole (ad blocking)
   - Home automation integration
   - Backup server

## Security Considerations

### Network Security
1. **Firewall Rules:**
   - Minimize open ports
   - Use secure protocols
   - Regular security audits

2. **Access Control:**
   - Strong password policy
   - 2FA where possible
   - Regular access review

### Data Protection
1. **Encryption:**
   - Enable disk encryption
   - Use HTTPS for remote access
   - Encrypted backups

2. **Privacy:**
   - Regular security updates
   - Monitor access logs
   - Implement fail2ban