# NexusController v2.0 - Enterprise Deployment Guide

This guide provides comprehensive deployment instructions for NexusController v2.0 across different environments, from development to enterprise production deployments.

## 📋 Prerequisites

### System Requirements

**Minimum Requirements:**
- Python 3.8+
- 2GB RAM
- 5GB disk space
- Ubuntu 18.04+ / Debian 10+ / CentOS 7+ / RHEL 7+

**Recommended Production:**
- Python 3.11+
- 8GB RAM
- 50GB disk space
- Ubuntu 22.04 LTS / RHEL 9

**Required System Packages:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk nmap ssh-keyscan tar openssl curl

# CentOS/RHEL
sudo yum install python3 python3-pip nmap openssh-clients tar openssl curl
# For GUI: sudo yum install tkinter

# Arch Linux
sudo pacman -S python python-pip nmap openssh tar openssl curl tk
```

## 🚀 Deployment Options

### 1. Quick Development Setup

**Single-Command Installation:**
```bash
cd ~/Skippy/app-to-deploy/NexusController
chmod +x nexus_launcher.sh
./nexus_launcher.sh
```

The launcher automatically:
- ✅ Checks system requirements
- ✅ Creates Python virtual environment
- ✅ Installs dependencies
- ✅ Sets up secure directories
- ✅ Validates configuration
- ✅ Launches GUI application

**Manual Installation:**
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Run system checks
python3 -c "import nexus_controller_v2; print('Core modules OK')"

# 3. Launch GUI
python3 nexus_gui.py

# 4. Or launch CLI
python3 nexus_controller_v2.py
```

### 2. Production Deployment

#### A. Traditional Server Deployment

**Step 1: Prepare Environment**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash nexus
sudo usermod -aG sudo nexus

# Switch to nexus user
sudo su - nexus

# Clone/copy NexusController
git clone /path/to/nexuscontroller /opt/nexuscontroller
cd /opt/nexuscontroller
```

**Step 2: Configure Production Settings**
```bash
# Create production configuration
mkdir -p ~/.nexus/config
cat > ~/.nexus/config/nexus.json << EOF
{
    "version": "2.0",
    "environment": "production",
    "network": {
        "default_range": "10.0.0.0/24",
        "scan_timeout": 120,
        "scan_rate_limit": 5
    },
    "security": {
        "ssh_timeout": 30,
        "session_timeout": 7200,
        "max_retries": 3
    },
    "logging": {
        "level": "INFO",
        "max_files": 30,
        "max_size": "100MB"
    }
}
EOF
chmod 600 ~/.nexus/config/nexus.json
```

**Step 3: Create Systemd Service**
```bash
sudo tee /etc/systemd/system/nexuscontroller.service << EOF
[Unit]
Description=NexusController Infrastructure Management
After=network.target
Wants=network.target

[Service]
Type=simple
User=nexus
Group=nexus
WorkingDirectory=/opt/nexuscontroller
Environment=PYTHONPATH=/opt/nexuscontroller
Environment=NEXUS_ENV=production
ExecStart=/opt/nexuscontroller/nexus_launcher.sh cli
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nexuscontroller

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/home/nexus/.nexus

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nexuscontroller
sudo systemctl start nexuscontroller

# Check status
sudo systemctl status nexuscontroller
```

#### B. Container Deployment

**Docker Deployment:**
```bash
# 1. Build container
docker build -t nexuscontroller:v2.0 .

# 2. Run container
docker run -d \
    --name nexuscontroller \
    --restart unless-stopped \
    -p 8080:8080 \
    -p 5901:5901 \
    -v nexus-data:/app/.nexus \
    -e NEXUS_ENV=production \
    -e LOG_LEVEL=INFO \
    nexuscontroller:v2.0

# 3. Check logs
docker logs nexuscontroller

# 4. Access GUI via VNC
# Connect to localhost:5901 with VNC client
# Default password: nexus123
```

**Docker Compose Deployment:**
```bash
# 1. Create production environment file
cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
VAULT_TOKEN=$(openssl rand -base64 32)
GRAFANA_PASSWORD=$(openssl rand -base64 32)
VNC_PASSWORD=$(openssl rand -base64 16)
NEXUS_ENV=production
LOG_LEVEL=INFO
EOF

# 2. Deploy full stack
docker-compose up -d

# 3. Check all services
docker-compose ps

# 4. View logs
docker-compose logs nexus-controller
```

#### C. Kubernetes Deployment

**Prerequisites:**
```bash
# Install kubectl and helm
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Create Kubernetes Manifests:**
```yaml
# nexus-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: nexuscontroller

---
# nexus-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nexus-config
  namespace: nexuscontroller
data:
  nexus.json: |
    {
      "version": "2.0",
      "environment": "production",
      "network": {
        "default_range": "10.0.0.0/24",
        "scan_timeout": 120,
        "scan_rate_limit": 10
      },
      "security": {
        "ssh_timeout": 30,
        "session_timeout": 3600,
        "max_retries": 3
      }
    }

---
# nexus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexuscontroller
  namespace: nexuscontroller
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nexuscontroller
  template:
    metadata:
      labels:
        app: nexuscontroller
    spec:
      containers:
      - name: nexuscontroller
        image: nexuscontroller:v2.0
        ports:
        - containerPort: 8080
        env:
        - name: NEXUS_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: nexus-config
          mountPath: /app/.nexus/config
        - name: nexus-data
          mountPath: /app/.nexus
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: nexus-config
        configMap:
          name: nexus-config
      - name: nexus-data
        persistentVolumeClaim:
          claimName: nexus-pvc

---
# nexus-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nexuscontroller-service
  namespace: nexuscontroller
spec:
  selector:
    app: nexuscontroller
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer

---
# nexus-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nexus-pvc
  namespace: nexuscontroller
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

**Deploy to Kubernetes:**
```bash
# 1. Apply manifests
kubectl apply -f nexus-namespace.yaml
kubectl apply -f nexus-configmap.yaml
kubectl apply -f nexus-deployment.yaml
kubectl apply -f nexus-service.yaml
kubectl apply -f nexus-pvc.yaml

# 2. Check deployment status
kubectl get pods -n nexuscontroller
kubectl get services -n nexuscontroller

# 3. Check logs
kubectl logs -f deployment/nexuscontroller -n nexuscontroller

# 4. Port forward for local access
kubectl port-forward service/nexuscontroller-service 8080:80 -n nexuscontroller
```

## 🔧 Configuration Management

### Environment Variables

**Core Configuration:**
```bash
export NEXUS_ENV=production              # Environment: development|production
export NEXUS_CONFIG_DIR=/app/.nexus      # Configuration directory
export NEXUS_NETWORK_RANGE=10.0.0.0/24  # Default network range
export NEXUS_SCAN_TIMEOUT=120            # Network scan timeout
export NEXUS_SSH_TIMEOUT=30              # SSH connection timeout
export LOG_LEVEL=INFO                    # Logging level
```

**Security Configuration:**
```bash
export NEXUS_SESSION_TIMEOUT=3600        # Session timeout (seconds)
export NEXUS_MAX_RETRIES=3               # Max connection retries
export NEXUS_SCAN_RATE_LIMIT=10          # Network scan rate limit
```

**API Server Configuration:**
```bash
export NEXUS_API_HOST=0.0.0.0            # API server host
export NEXUS_API_PORT=8080               # API server port
export NEXUS_API_DEBUG=false             # API debug mode
```

### Configuration Files

**Main Configuration (`~/.nexus/config/nexus.json`):**
```json
{
    "version": "2.0",
    "environment": "production",
    "created": "2024-01-01T00:00:00Z",
    "network": {
        "default_range": "10.0.0.0/24",
        "scan_timeout": 120,
        "scan_rate_limit": 10
    },
    "security": {
        "ssh_timeout": 30,
        "session_timeout": 3600,
        "max_retries": 3
    },
    "ui": {
        "theme": "dark",
        "geometry": "1200x800"
    },
    "logging": {
        "level": "INFO",
        "max_files": 30,
        "max_size": "100MB"
    },
    "features": {
        "api_server": true,
        "cloud_integration": true,
        "auto_backup": true
    }
}
```

**Cloud Providers (`~/.nexus/config/cloud_providers.json` - encrypted):**
```json
{
    "google_drive": {
        "enabled": true,
        "sync_path": "/home/user/GoogleDrive",
        "backup_path": "NexusBackups",
        "credentials_file": "/path/to/credentials.json"
    },
    "aws": {
        "enabled": false,
        "region": "us-east-1",
        "access_key_id": "encrypted_access_key",
        "secret_access_key": "encrypted_secret_key"
    },
    "github": {
        "enabled": true,
        "username": "your_username",
        "token": "encrypted_token",
        "repositories": ["nexus-configs", "nexus-scripts"]
    }
}
```

## 🔒 Security Hardening

### SSL/TLS Configuration

**Generate SSL Certificates:**
```bash
# Create SSL directory
mkdir -p ~/.nexus/ssl

# Generate self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout ~/.nexus/ssl/key.pem \
    -out ~/.nexus/ssl/cert.pem -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=nexuscontroller.local"

# Set proper permissions
chmod 600 ~/.nexus/ssl/key.pem
chmod 644 ~/.nexus/ssl/cert.pem
```

**Production SSL with Let's Encrypt:**
```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d nexuscontroller.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/nexuscontroller.yourdomain.com/privkey.pem ~/.nexus/ssl/key.pem
sudo cp /etc/letsencrypt/live/nexuscontroller.yourdomain.com/fullchain.pem ~/.nexus/ssl/cert.pem
sudo chown nexus:nexus ~/.nexus/ssl/*.pem
```

### Firewall Configuration

**UFW Configuration:**
```bash
# Enable UFW
sudo ufw enable

# Allow SSH (adjust port as needed)
sudo ufw allow 22/tcp

# Allow NexusController API (production only)
sudo ufw allow 8080/tcp

# Allow VNC (secure networks only)
sudo ufw allow from 10.0.0.0/8 to any port 5901

# Allow monitoring (internal networks only)
sudo ufw allow from 10.0.0.0/8 to any port 3000
sudo ufw allow from 10.0.0.0/8 to any port 9090

# Check status
sudo ufw status verbose
```

**iptables Configuration:**
```bash
# Create comprehensive firewall rules
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5901 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -j DROP

# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

### Access Control

**SSH Key Management:**
```bash
# Generate dedicated SSH key for NexusController
ssh-keygen -t ed25519 -f ~/.nexus/keys/nexus_ssh_key -N ""

# Set proper permissions
chmod 600 ~/.nexus/keys/nexus_ssh_key
chmod 644 ~/.nexus/keys/nexus_ssh_key.pub

# Copy public key to target servers
ssh-copy-id -i ~/.nexus/keys/nexus_ssh_key.pub user@target-server
```

**API Key Management:**
```bash
# Generate API key for integration
python3 -c "
from nexus_api_server import NexusAPIServer
server = NexusAPIServer()
api_key = server.api_key_manager.create_api_key('integration', ['network:read', 'system:read'])
print(f'API Key: {api_key}')
"
```

## 📊 Monitoring and Observability

### Log Management

**Configure Log Rotation:**
```bash
sudo tee /etc/logrotate.d/nexuscontroller << EOF
/home/nexus/.nexus/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 nexus nexus
    postrotate
        systemctl reload nexuscontroller || true
    endscript
}
EOF
```

**Centralized Logging with rsyslog:**
```bash
# Configure rsyslog
sudo tee /etc/rsyslog.d/nexuscontroller.conf << EOF
# NexusController logs
\$template NexusFormat,"%timestamp% %hostname% nexus: %msg%\n"
:programname, isequal, "nexuscontroller" /var/log/nexuscontroller.log;NexusFormat
& stop
EOF

sudo systemctl restart rsyslog
```

### Metrics and Alerting

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "nexus_rules.yml"

scrape_configs:
  - job_name: 'nexuscontroller'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "NexusController Infrastructure",
    "panels": [
      {
        "title": "System Metrics",
        "type": "graph",
        "targets": [
          {
            "expr": "nexus_cpu_usage",
            "legendFormat": "CPU Usage"
          },
          {
            "expr": "nexus_memory_usage",
            "legendFormat": "Memory Usage"
          }
        ]
      },
      {
        "title": "Network Activity",
        "type": "graph",
        "targets": [
          {
            "expr": "nexus_network_scans_total",
            "legendFormat": "Network Scans"
          },
          {
            "expr": "nexus_ssh_connections_active",
            "legendFormat": "Active SSH Connections"
          }
        ]
      }
    ]
  }
}
```

## 🔄 Backup and Recovery

### Automated Backup Strategy

**Create Backup Script:**
```bash
#!/bin/bash
# nexus_backup.sh - Automated backup script

BACKUP_DIR="/opt/backups/nexuscontroller"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup NexusController data
tar -czf "$BACKUP_DIR/nexus_backup_$DATE.tar.gz" \
    -C /home/nexus \
    .nexus/config \
    .nexus/keys \
    .nexus/logs

# Backup database (if using PostgreSQL)
if command -v pg_dump >/dev/null 2>&1; then
    pg_dump nexuscontroller > "$BACKUP_DIR/nexus_db_$DATE.sql"
fi

# Remove old backups
find "$BACKUP_DIR" -name "nexus_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "nexus_db_*.sql" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/nexus_backup_$DATE.tar.gz"
```

**Schedule with Crontab:**
```bash
# Add to crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /opt/scripts/nexus_backup.sh
```

### Disaster Recovery

**Recovery Procedure:**
```bash
# 1. Stop NexusController service
sudo systemctl stop nexuscontroller

# 2. Restore configuration and data
cd /home/nexus
tar -xzf /opt/backups/nexuscontroller/nexus_backup_YYYYMMDD_HHMMSS.tar.gz

# 3. Restore database (if applicable)
psql nexuscontroller < /opt/backups/nexuscontroller/nexus_db_YYYYMMDD_HHMMSS.sql

# 4. Fix permissions
chown -R nexus:nexus .nexus
chmod -R 700 .nexus

# 5. Start service
sudo systemctl start nexuscontroller

# 6. Verify functionality
sudo systemctl status nexuscontroller
```

## 🧪 Testing and Validation

### Pre-Deployment Testing

**Run Test Suite:**
```bash
# Full test suite
python3 test_nexus.py -v

# Specific test categories
python3 -m unittest test_nexus.TestSecurityManager -v
python3 -m unittest test_nexus.TestNetworkDiscovery -v
python3 -m unittest test_nexus.TestSSHManager -v
```

**Integration Testing:**
```bash
# Test network connectivity
./nexus_launcher.sh check

# Test API endpoints
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8080/api/v1/system/info

# Test GUI launch
DISPLAY=:99 python3 nexus_gui.py --test
```

### Performance Testing

**Load Testing Script:**
```bash
#!/bin/bash
# load_test.sh - Basic load testing

API_BASE="http://localhost:8080/api/v1"
API_KEY="your_api_key"

# Test concurrent network scans
for i in {1..10}; do
    curl -X POST \
         -H "Authorization: Bearer $API_KEY" \
         -H "Content-Type: application/json" \
         -d '{"network_range":"192.168.1.0/24"}' \
         "$API_BASE/network/scan" &
done

wait
echo "Load test completed"
```

## 🚨 Troubleshooting

### Common Issues

**1. GUI Won't Start:**
```bash
# Check X11 display
echo $DISPLAY
export DISPLAY=:0

# Install GUI dependencies
sudo apt install python3-tk xvfb

# Test with virtual display
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
python3 nexus_gui.py
```

**2. Network Scan Fails:**
```bash
# Check nmap installation
which nmap || sudo apt install nmap

# Test nmap manually
nmap -sn 10.0.0.0/24

# Check permissions
sudo setcap cap_net_raw=ep $(which nmap)
```

**3. SSH Connection Issues:**
```bash
# Check SSH client
ssh -V

# Test connection manually
ssh -i ~/.nexus/keys/nexus_ssh_key user@target

# Check host keys
ssh-keyscan target-host
```

**4. API Server Issues:**
```bash
# Check port availability
netstat -tlnp | grep 8080

# Check logs
tail -f ~/.nexus/logs/api_$(date +%Y%m%d).log

# Test API manually
curl http://localhost:8080/health
```

### Debug Mode

**Enable Debug Logging:**
```bash
export LOG_LEVEL=DEBUG
python3 nexus_gui.py
```

**Verbose Launcher:**
```bash
bash -x ./nexus_launcher.sh
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review system logs
- Check backup integrity
- Update security patches
- Monitor disk usage

**Monthly:**
- Rotate API keys
- Update dependencies
- Review access logs
- Performance analysis

**Quarterly:**
- Security audit
- Disaster recovery test
- Documentation updates
- Capacity planning

### Getting Help

**Log Locations:**
- Application: `~/.nexus/logs/nexus_YYYYMMDD.log`
- API Server: `~/.nexus/logs/api_YYYYMMDD.log`
- System: `/var/log/syslog` or `journalctl -u nexuscontroller`

**Diagnostic Commands:**
```bash
# System information
./nexus_launcher.sh check

# Service status
sudo systemctl status nexuscontroller

# Container logs
docker logs nexuscontroller

# Kubernetes logs
kubectl logs deployment/nexuscontroller -n nexuscontroller
```

---

**NexusController v2.0** - *Enterprise Infrastructure Management Made Simple*

For additional support, consult the main README_v2.md or check the project repository for updates and community discussions.