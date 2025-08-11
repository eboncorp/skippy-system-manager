#!/bin/bash
# Comprehensive Ethereum Node Setup Script for Ubuntu Server
set -euo pipefail

# Set variables
TARGET_DISK="/dev/nvme0n1"
MOUNT_POINT="/mnt/ethereum_node"
HOSTNAME="ebon-eth"
USERNAME="dave"
SSH_PORT=2222
EMAIL="eboncorp@gmail.com"
DOMAIN="eboneth.ddns.net"
LOG_FILE="/tmp/ethereum_node_setup.log"
CHROOT_LOG_FILE="/tmp/chroot_script.log"
ETHEREUM_NETWORK="mainnet"
GETH_DATA_DIR="/var/lib/goethereum"
PRYSM_DATA_DIR="/var/lib/prysm"
BACKUP_DIR="/var/backups/ethereum"
NOIP_USERNAME="eboncorp"
NOIP_PASSWORD="REDACTED_SERVER_PASSWORD"  # Consider using an environment variable for this in production

# Function to log messages
log_message() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

# Function to check command success
check_command() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1"
        exit 1
    fi
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    local line_number=${1:-"unknown"}
    log_message "Error occurred at line $line_number. Exit code: $exit_code"
    log_message "Cleaning up..."
    umount -R "$MOUNT_POINT" || true
    exit $exit_code
}

# Trap to catch and log errors
trap 'handle_error $LINENO' ERR

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
   log_message "This script must be run as root" 
   exit 1
fi

# Check for required commands
for cmd in parted mkfs.ext4 mkfs.fat debootstrap blkid; do
    if ! command -v $cmd &> /dev/null; then
        log_message "Error: $cmd is required but not installed. Aborting."
        exit 1
    fi
done

# Check internet connectivity
if ! ping -c 1 google.com &> /dev/null; then
    log_message "No internet connectivity. Please check your connection and try again."
    exit 1
fi

# Check for sufficient disk space
log_message "Checking disk space..."
TOTAL_SPACE=$(lsblk -bdno SIZE "${TARGET_DISK}" | numfmt --to=iec --format="%.0f")
TOTAL_SPACE_GB=$(echo "${TOTAL_SPACE}" | sed 's/G//')

log_message "Debug: Detected total space: ${TOTAL_SPACE} (${TOTAL_SPACE_GB}GB) on ${TARGET_DISK}"

if [ "${TOTAL_SPACE_GB}" -lt 500 ]; then
    log_message "Error: Insufficient disk space. At least 500GB is required for a full Ethereum node."
    exit 1
else
    log_message "Sufficient disk space available: ${TOTAL_SPACE}"
fi

# Confirmation prompt
echo "This script will partition and format ${TARGET_DISK}."
echo "All data on ${TARGET_DISK} will be lost."
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_message "Operation cancelled by user"
    exit 1
fi

# Main script starts here
log_message "Starting Ethereum full node setup script"

# Partition and format the disk
show_progress "Partitioning and formatting $TARGET_DISK"
parted -s "$TARGET_DISK" mklabel gpt
parted -s "$TARGET_DISK" mkpart primary fat32 1MiB 512MiB
parted -s "$TARGET_DISK" set 1 esp on
parted -s "$TARGET_DISK" mkpart primary ext4 512MiB 100%
finish_progress

# Format partitions
show_progress "Formatting partitions"
mkfs.fat -F32 "${TARGET_DISK}p1"
mkfs.ext4 "${TARGET_DISK}p2"
finish_progress

# Mount the target system
show_progress "Mounting partitions"
mount "${TARGET_DISK}p2" "$MOUNT_POINT"
mkdir -p "$MOUNT_POINT/boot/efi"
mount "${TARGET_DISK}p1" "$MOUNT_POINT/boot/efi"
finish_progress

# Install the base system
show_progress "Installing base system"
debootstrap --arch amd64 focal "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu
finish_progress

# Generate fstab
log_message "Generating fstab..."
mkdir -p "$MOUNT_POINT/etc"
{
    echo "# /etc/fstab: static file system information."
    echo "# Use 'blkid' to print the universally unique identifier for a device."
    echo "#"
    echo "# <file system>             <mount point>   <type>  <options>       <dump>  <pass>"
    echo "UUID=$(blkid -s UUID -o value ${TARGET_DISK}p2) /               ext4    errors=remount-ro 0       1"
    echo "UUID=$(blkid -s UUID -o value ${TARGET_DISK}p1) /boot/efi       vfat    umask=0077      0       1"
    echo "/swapfile                   none            swap    sw              0       0"
} > "$MOUNT_POINT/etc/fstab"

# Create a swapfile
show_progress "Creating swapfile"
dd if=/dev/zero of="$MOUNT_POINT/swapfile" bs=1M count=8192  # 8GB swap
chmod 600 "$MOUNT_POINT/swapfile"
mkswap "$MOUNT_POINT/swapfile"
finish_progress

# Prepare chroot environment
show_progress "Preparing chroot environment"
mount -t proc /proc "$MOUNT_POINT/proc"
mount --rbind /sys "$MOUNT_POINT/sys"
mount --make-rslave "$MOUNT_POINT/sys"
mount --rbind /dev "$MOUNT_POINT/dev"
mount --make-rslave "$MOUNT_POINT/dev"
cp /etc/resolv.conf "$MOUNT_POINT/etc/resolv.conf"
finish_progress

# Create the post-installation script
log_message "Creating post-installation script..."
cat > "$MOUNT_POINT/root/post_install.sh" << EOL
#!/bin/bash
set -euo pipefail

# Redirect output to log file
exec > >(tee -a "$CHROOT_LOG_FILE") 2>&1

# Set variables
HOSTNAME="${HOSTNAME}"
USERNAME="${USERNAME}"
SSH_PORT=${SSH_PORT}
EMAIL="${EMAIL}"
DOMAIN="${DOMAIN}"
GETH_DATA_DIR="${GETH_DATA_DIR}"
PRYSM_DATA_DIR="${PRYSM_DATA_DIR}"
BACKUP_DIR="${BACKUP_DIR}"
NOIP_USERNAME="${NOIP_USERNAME}"
NOIP_PASSWORD="${NOIP_PASSWORD}"

echo "Starting post-installation script..."

# Set up system
echo "Setting up system..."
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
dpkg-reconfigure -f noninteractive tzdata
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
echo \$HOSTNAME > /etc/hostname

# Update sources.list
cat > /etc/apt/sources.list << EOSOURCES
deb http://archive.ubuntu.com/ubuntu focal main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu focal-security main restricted universe multiverse
EOSOURCES

# Update and install packages
echo "Updating and installing packages..."
apt update
apt install -y software-properties-common curl wget git ufw unattended-upgrades apt-listchanges \
    fail2ban prometheus prometheus-node-exporter nginx certbot python3-certbot-nginx

# Install Grafana
echo "deb https://packages.grafana.com/oss/deb stable main" | tee /etc/apt/sources.list.d/grafana.list
wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
apt update
apt install -y grafana

# Upgrade all packages
apt upgrade -y

# Configure automatic updates
echo "Configuring automatic updates..."
echo 'Unattended-Upgrade::Automatic-Reboot "true";' >> /etc/apt/apt.conf.d/50unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot-Time "02:00";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# Install and configure GRUB
echo "Installing and configuring GRUB..."
apt install -y grub-efi-amd64
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu
update-grub

# Create user and configure SSH
echo "Creating user and configuring SSH..."
useradd -m -s /bin/bash \$USERNAME
echo "\$USERNAME:\$(openssl rand -base64 12)" | chpasswd
usermod -aG sudo \$USERNAME
sed -i "s/#Port 22/Port \$SSH_PORT/" /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Set up firewall
echo "Setting up firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow \$SSH_PORT/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 30303/tcp
ufw allow 30303/udp
ufw allow 13000/tcp
ufw allow 12000/udp
ufw --force enable

# Configure fail2ban
echo "Configuring fail2ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sed -i 's/bantime  = 10m/bantime  = 1h/' /etc/fail2ban/jail.local
sed -i 's/findtime  = 10m/findtime  = 20m/' /etc/fail2ban/jail.local
sed -i 's/maxretry = 5/maxretry = 3/' /etc/fail2ban/jail.local

# Install Geth
echo "Installing Geth..."
add-apt-repository -y ppa:ethereum/ethereum
apt update
apt install -y ethereum

# Install Prysm
echo "Installing Prysm..."
mkdir -p /usr/local/bin
curl https://raw.githubusercontent.com/prysmaticlabs/prysm/master/prysm.sh --output /usr/local/bin/prysm.sh
chmod +x /usr/local/bin/prysm.sh

# Create Geth systemd service
echo "Creating Geth systemd service..."
cat > /etc/systemd/system/geth.service <<EOLS
[Unit]
Description=Ethereum Go Client
After=network.target

[Service]
User=\$USERNAME
ExecStart=/usr/bin/geth --datadir \$GETH_DATA_DIR --http --http.addr 0.0.0.0 --http.vhosts=* --http.api eth,net,web3 --ws --ws.addr 0.0.0.0 --ws.origins=* --cache 16384 --maxpeers 50
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOLS

# Create Prysm beacon chain systemd service
echo "Creating Prysm beacon chain systemd service..."
cat > /etc/systemd/system/prysm-beacon-chain.service <<EOLS
[Unit]
Description=Prysm Ethereum 2.0 Beacon Chain
Wants=network-online.target
After=network-online.target

[Service]
User=\$USERNAME
ExecStart=/usr/local/bin/prysm.sh beacon-chain --datadir=\$PRYSM_DATA_DIR --http-web3provider=http://localhost:8545
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOLS

# Set up Ethereum data directories and log rotation
echo "Setting up Ethereum data directories and log rotation..."
mkdir -p \$GETH_DATA_DIR \$PRYSM_DATA_DIR
chown -R \$USERNAME:\$USERNAME \$GETH_DATA_DIR \$PRYSM_DATA_DIR
cat > /etc/logrotate.d/ethereum <<EOLS
\$GETH_DATA_DIR/geth.log \$PRYSM_DATA_DIR/beacon-chain.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 \$USERNAME \$USERNAME
}
EOLS

# Set up Nginx as reverse proxy
echo "Setting up Nginx as reverse proxy..."
cat > /etc/nginx/sites-available/ethereum <<EOLS
server {
    listen 443 ssl http2;
    server_name \$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/\$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/\$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout  10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://localhost:8545;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /beacon/ {
        proxy_pass http://localhost:3500/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http
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
