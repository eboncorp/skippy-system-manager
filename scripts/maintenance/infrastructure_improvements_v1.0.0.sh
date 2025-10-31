#\!/bin/bash
# NexusController Infrastructure Improvements

echo "🔧 IMPLEMENTING INFRASTRUCTURE IMPROVEMENTS"
echo "=========================================="

echo "Phase 1: Security & Performance Hardening"

# 1. Enable UFW firewall with proper rules
echo "⚡ Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8000/tcp comment 'NexusController API'
sudo ufw allow from 10.0.0.0/24 to any port 8000 comment 'Local network only'

# 2. Docker security hardening
echo "🐳 Hardening Docker..."
sudo tee /etc/docker/daemon.json << 'DOCKER_EOF'
{
  "icc": false,
  "userland-proxy": false,
  "no-new-privileges": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
DOCKER_EOF

# 3. System security hardening
echo "🔒 Applying system hardening..."
sudo tee -a /etc/sysctl.conf << 'SYSCTL_EOF'

# NexusController Security Hardening
net.ipv4.ip_forward=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.all.accept_redirects=0
kernel.dmesg_restrict=1
SYSCTL_EOF

sudo sysctl -p

# 4. Install fail2ban for intrusion prevention
echo "🛡️ Installing fail2ban..."
sudo apt update && sudo apt install -y fail2ban
sudo systemctl enable fail2ban

# 5. Create monitoring alerts
echo "📊 Setting up monitoring alerts..."
mkdir -p /home/dave/monitoring
cat > /home/dave/monitoring/check_services.sh << 'MONITOR_EOF'
#\!/bin/bash
# Service health check with alerts

CRITICAL_SERVICES=("docker" "ssh")
MEDIA_SERVER="10.0.0.29"

for service in "${CRITICAL_SERVICES[@]}"; do
    if \! systemctl is-active --quiet "$service"; then
        echo "ALERT: $service is down on $(hostname)" | logger -t nexus-monitor
    fi
done

# Check media server connectivity
if \! ping -c 1 -W 2 "$MEDIA_SERVER" > /dev/null 2>&1; then
    echo "ALERT: Media server $MEDIA_SERVER unreachable" | logger -t nexus-monitor
fi
MONITOR_EOF

chmod +x /home/dave/monitoring/check_services.sh

# 6. Add to crontab for regular checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/dave/monitoring/check_services.sh") | crontab -

echo ""
echo "✅ Phase 1 improvements completed\!"
echo ""
echo "Next Steps:"
echo "1. Restart Docker: sudo systemctl restart docker"
echo "2. Test firewall: sudo ufw status verbose"
echo "3. Check monitoring: tail -f /var/log/syslog | grep nexus-monitor"
echo ""
echo "🔐 Security improvements active\!"
