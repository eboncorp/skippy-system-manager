proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOLS

ln -s /etc/nginx/sites-available/ethereum /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Install and configure Certbot
echo "Installing and configuring Certbot..."
certbot --nginx -d \$DOMAIN --non-interactive --agree-tos -m \$EMAIL

# Set up automatic SSL renewal
echo "Setting up automatic SSL renewal..."
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | tee -a /etc/crontab > /dev/null

# Install and configure No-IP Dynamic Update Client (DUC)
echo "Installing No-IP Dynamic Update Client..."
cd /tmp
wget https://www.noip.com/client/linux/noip-duc-linux.tar.gz
tar xf noip-duc-linux.tar.gz
cd noip-*
make install
/usr/local/bin/noip2 -C -c /tmp/no-ip2.conf -U 5 -u \$NOIP_USERNAME -p \$NOIP_PASSWORD -Y

# Create a systemd service for No-IP DUC
echo "Creating systemd service for No-IP DUC..."
cat > /etc/systemd/system/noip.service <<EOLS
[Unit]
Description=No-IP Dynamic DNS Update Client
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/noip2
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOLS

# Set up Prometheus configuration
echo "Setting up Prometheus configuration..."
cat > /etc/prometheus/prometheus.yml <<EOLS
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'geth'
    metrics_path: /debug/metrics/prometheus
    static_configs:
      - targets: ['localhost:6060']

  - job_name: 'prysm'
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8080']
EOLS

# Set up Grafana
echo "Setting up Grafana..."
sed -i 's/;domain = localhost/domain = \$DOMAIN/' /etc/grafana/grafana.ini
sed -i 's/;root_url = %(protocol)s://%(domain)s:%(http_port)s//root_url = %(protocol)s://%(domain)s/grafana/' /etc/grafana/grafana.ini

# Enable and start services
echo "Enabling and starting services..."
systemctl enable geth prysm-beacon-chain prometheus prometheus-node-exporter grafana-server noip nginx
systemctl start geth prysm-beacon-chain prometheus prometheus-node-exporter grafana-server noip nginx

# Set up basic security measures
echo "Setting up basic security measures..."
# Disable root login
passwd -l root

# Secure shared memory
echo "tmpfs     /run/shm     tmpfs     defaults,noexec,nosuid     0     0" >> /etc/fstab

# Secure /tmp
echo "tmpfs     /tmp     tmpfs     defaults,noexec,nosuid     0     0" >> /etc/fstab

# Harden sysctl settings
cat >> /etc/sysctl.conf <<EOLS
# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP broadcast requests
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0 
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Block SYN attacks
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Log Martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0 
net.ipv6.conf.default.accept_redirects = 0

# Ignore Directed pings
net.ipv4.icmp_echo_ignore_all = 1
EOLS

sysctl -p

echo "Post-installation script completed."
EOL

# Make the post-installation script executable
chmod +x "$MOUNT_POINT/root/post_install.sh"

# Chroot into the new system and run the post-installation script
show_progress "Chrooting into the new system and running post-installation script"
chroot "$MOUNT_POINT" /root/post_install.sh
finish_progress

# Backup important configuration files
log_message "Backing up important configuration files..."
mkdir -p "$MOUNT_POINT/root/config_backups"
cp "$MOUNT_POINT/etc/fstab" "$MOUNT_POINT/root/config_backups/"
cp "$MOUNT_POINT/etc/ssh/sshd_config" "$MOUNT_POINT/root/config_backups/"
cp "$MOUNT_POINT/etc/systemd/system/geth.service" "$MOUNT_POINT/root/config_backups/"
cp "$MOUNT_POINT/etc/systemd/system/prysm-beacon-chain.service" "$MOUNT_POINT/root/config_backups/"
cp "$MOUNT_POINT/etc/nginx/sites-available/ethereum" "$MOUNT_POINT/root/config_backups/"

# Unmount all mounted partitions
show_progress "Unmounting partitions"
umount -R "$MOUNT_POINT"
finish_progress

# Preserve setup logs
log_message "Preserving setup logs..."
mkdir -p "$MOUNT_POINT/var/log/ethereum_setup"
cp "$LOG_FILE" "$MOUNT_POINT/var/log/ethereum_setup/main_setup.log"
cp "$MOUNT_POINT$CHROOT_LOG_FILE" "$MOUNT_POINT/var/log/ethereum_setup/chroot_setup.log"

log_message "Ethereum node setup completed successfully."
echo "============================================================"
echo "Ethereum Full Node Setup Complete"
echo "============================================================"
echo "Your Ethereum full node has been set up successfully."
echo "Please reboot your system to start using your new Ethereum node."
echo "After rebooting, you can SSH into your node using:"
echo "ssh -p $SSH_PORT $USERNAME@$DOMAIN"
echo "Remember to update your SSH client configuration if needed."
echo "Setup logs have been preserved in /var/log/ethereum_setup/"
echo "Important configuration files have been backed up to /root/config_backups/"
echo "============================================================"
echo "Next steps:"
echo "1. Set up a strong password for your Grafana admin account"
echo "2. Import Ethereum dashboards into Grafana"
echo "3. Configure alerts in Prometheus/Grafana"
echo "4. Regularly check for updates to Geth and Prysm"
echo "5. Monitor your node's performance and sync status"
echo "============================================================"
