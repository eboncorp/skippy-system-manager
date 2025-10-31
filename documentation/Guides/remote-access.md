# Remote Access and Security Configuration

## Dynamic DNS Setup

### 1. DuckDNS Configuration
```bash
# Create DNS record
1. Register at duckdns.org
2. Create subdomain: yourdomain.duckdns.org
3. Note your token

# Update script (runs every 5 minutes)
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=yourdomain&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -

# Crontab entry
*/5 * * * * ~/duckdns/duck.sh
```

### 2. Router Port Forwarding
```plaintext
Required Ports:
- Plex: 32400 TCP
- NextCloud: 443 TCP
- SSH (optional): 22 TCP
- WireGuard: 51820 UDP

Port Forwarding Rules:
External Port -> Internal IP -> Internal Port -> Protocol
32400 -> NAS_IP -> 32400 -> TCP
443 -> NAS_IP -> 443 -> TCP
51820 -> NAS_IP -> 51820 -> UDP
```

## SSL Certificate Setup

### 1. Let's Encrypt with Nginx Proxy Manager
```yaml
# Nginx Proxy Host Configuration
Domain Names: yourdomain.duckdns.org
Scheme: https
Forward Hostname/IP: NAS_IP
Forward Port: 443

SSL Configuration:
- Request new SSL Certificate
- Force SSL
- HTTP/2 Support: Enabled
- HSTS: Enabled
- Custom SSL Config:
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
```

## VPN Server Configuration

### 1. WireGuard Setup
```ini
# /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = server_private_key

# Client 1
[Peer]
PublicKey = client1_public_key
AllowedIPs = 10.0.0.2/32

# Client 2
[Peer]
PublicKey = client2_public_key
AllowedIPs = 10.0.0.3/32
```

### 2. Client Configuration
```ini
# client.conf
[Interface]
PrivateKey = client_private_key
Address = 10.0.0.2/32
DNS = 10.0.0.1

[Peer]
PublicKey = server_public_key
Endpoint = yourdomain.duckdns.org:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

## Firewall Configuration

### 1. UFW Rules (Ubuntu)
```bash
# Base rules
ufw default deny incoming
ufw default allow outgoing

# Allow specific services
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw allow 32400/tcp # Plex
ufw allow 51820/udp # WireGuard

# Enable firewall
ufw enable
```

### 2. Fail2ban Configuration
```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 24h

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
```

## Mobile App Configuration

### 1. Plex Mobile Setup
```plaintext
Direct Connection:
- Enable Custom server access
- Server: yourdomain.duckdns.org:32400
- Enable Direct Play
- Enable Direct Stream
- Quality on Cellular: 720p 2Mbps
- Quality on WiFi: Maximum
```

### 2. NextCloud Mobile Setup
```plaintext
Server Address: https://yourdomain.duckdns.org
Enable Auto-upload:
- Camera folder
- Select folders to sync
- Background sync enabled
- Cellular data backup (optional)
```

### 3. WireGuard Mobile Setup
```plaintext
1. Generate QR code from server config
2. Scan QR code in WireGuard app
3. Configure Split Tunneling:
   - Allow LAN access
   - Exclude selected apps
4. Enable Always-on VPN (optional)
```

## Monitoring and Alerts

### 1. Email Alerts Configuration
```yaml
# Docker Compose for Watchtower (automated updates)
version: '3'
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_NOTIFICATIONS=email
      - WATCHTOWER_NOTIFICATION_EMAIL_FROM=your@email.com
      - WATCHTOWER_NOTIFICATION_EMAIL_TO=your@email.com
      - WATCHTOWER_NOTIFICATION_EMAIL_SERVER=smtp.gmail.com
      - WATCHTOWER_NOTIFICATION_EMAIL_SERVER_PORT=587
      - WATCHTOWER_NOTIFICATION_EMAIL_SERVER_USER=your@email.com
      - WATCHTOWER_NOTIFICATION_EMAIL_SERVER_PASSWORD=your_password
      - WATCHTOWER_NOTIFICATION_EMAIL_DELAY=2
```

### 2. Health Check Configuration
```yaml
# Docker Compose for Healthchecks
version: '3'
services:
  healthchecks:
    image: linuxserver/healthchecks
    ports:
      - 8000:8000
    volumes:
      - /volume1/docker/healthchecks:/config
    environment:
      - SITE_ROOT=https://hc.yourdomain.com
      - DEFAULT_FROM_EMAIL=alerts@yourdomain.com
      - EMAIL_HOST=smtp.gmail.com
      - EMAIL_PORT=587
      - EMAIL_HOST_USER=your@email.com
      - EMAIL_HOST_PASSWORD=your_password
```

## Backup Strategy

### 1. Local Backup Configuration
```bash
#!/bin/bash
# Daily incremental backup script

SOURCE="/volume1/media"
BACKUP="/volume1/backup"
DATE=$(date +%Y-%m-%d)

# Create incremental backup
rsync -av --link-dest=$BACKUP/latest $SOURCE $BACKUP/$DATE

# Update latest symlink
rm -f $BACKUP/latest
ln -s $BACKUP/$DATE $BACKUP/latest
```

### 2. Cloud Backup Setup (rclone)
```bash
# rclone.conf
[gdrive]
type = drive
client_id = your_client_id
client_secret = your_client_secret
scope = drive
token = {"access_token":"xxx","token_type":"Bearer","refresh_token":"xxx"}

# Backup script
#!/bin/bash
rclone sync /volume1/important gdrive:backup/nas --progress
```
