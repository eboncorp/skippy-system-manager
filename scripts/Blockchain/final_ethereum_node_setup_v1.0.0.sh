#!/bin/bash
# Comprehensive Ethereum Node Setup Script for Ubuntu with No-IP DUC
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
ETHEREUM_NETWORK="mainnet"
GETH_DATA_DIR="/var/lib/goethereum"
BACKUP_DIR="/var/backups/ethereum"
NOIP_USERNAME="eboncorp"
NOIP_PASSWORD="YOUR_NOIP_PASSWORD"  # Replace this with your actual No-IP password

# Function to log messages
log_message() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
   log_message "This script must be run as root" 
   exit 1
fi

# Check internet connectivity
if ! ping -c 1 google.com &> /dev/null; then
    log_message "No internet connectivity. Please check your connection and try again."
    exit 1
fi

# Update and install necessary packages
log_message "Updating and installing necessary packages..."
apt update && apt install -y debootstrap

# Partition and format the disk
log_message "Partitioning and formatting $TARGET_DISK..."
parted -s "$TARGET_DISK" mklabel gpt
parted -s "$TARGET_DISK" mkpart primary fat32 1MiB 512MiB
parted -s "$TARGET_DISK" set 1 esp on
parted -s "$TARGET_DISK" mkpart primary ext4 512MiB 100%
mkfs.fat -F32 "${TARGET_DISK}p1"
mkfs.ext4 "${TARGET_DISK}p2"

# Mount the target system
log_message "Mounting partitions..."
mkdir -p "$MOUNT_POINT"
mount "${TARGET_DISK}p2" "$MOUNT_POINT"
mkdir -p "$MOUNT_POINT/boot/efi"
mount "${TARGET_DISK}p1" "$MOUNT_POINT/boot/efi"

# Install the base system
log_message "Installing base system..."
debootstrap --arch amd64 focal "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu

# Generate fstab
log_message "Generating fstab..."
genfstab -U "$MOUNT_POINT" >> "$MOUNT_POINT/etc/fstab"

# Prepare chroot environment
log_message "Preparing chroot environment..."
mount -t proc /proc "$MOUNT_POINT/proc"
mount --rbind /sys "$MOUNT_POINT/sys"
mount --make-rslave "$MOUNT_POINT/sys"
mount --rbind /dev "$MOUNT_POINT/dev"
mount --make-rslave "$MOUNT_POINT/dev"
cp /etc/resolv.conf "$MOUNT_POINT/etc/resolv.conf"

# Create the post-installation script
log_message "Creating post-installation script..."
cat > "$MOUNT_POINT/root/post_install.sh" << EOL
#!/bin/bash
set -euo pipefail

# Set variables
HOSTNAME="$HOSTNAME"
USERNAME="$USERNAME"
SSH_PORT=$SSH_PORT
EMAIL="$EMAIL"
DOMAIN="$DOMAIN"
GETH_DATA_DIR="$GETH_DATA_DIR"
BACKUP_DIR="$BACKUP_DIR"
NOIP_USERNAME="$NOIP_USERNAME"
NOIP_PASSWORD="$NOIP_PASSWORD"

# Set up system
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
dpkg-reconfigure -f noninteractive tzdata
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
echo \$HOSTNAME > /etc/hostname

# Update and install packages
apt update && apt upgrade -y
apt install -y linux-image-generic grub-efi-amd64 ubuntu-standard \
    software-properties-common curl git ufw fail2ban \
    prometheus prometheus-node-exporter grafana \
    unattended-upgrades apt-listchanges miniupnpc

# Configure automatic updates
echo 'Unattended-Upgrade::Automatic-Reboot "true";' >> /etc/apt/apt.conf.d/50unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot-Time "02:00";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# Install and configure GRUB
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu
update-grub

# Create user and configure SSH
useradd -m -s /bin/bash \$USERNAME
echo "\$USERNAME:\$(openssl rand -base64 12)" | chpasswd
usermod -aG sudo \$USERNAME
sed -i "s/#Port 22/Port \$SSH_PORT/" /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Set up firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow \$SSH_PORT/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 30303/tcp
ufw allow 30303/udp
ufw --force enable

# Configure fail2ban
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sed -i 's/bantime  = 10m/bantime  = 1h/' /etc/fail2ban/jail.local
sed -i 's/findtime  = 10m/findtime  = 20m/' /etc/fail2ban/jail.local
sed -i 's/maxretry = 5/maxretry = 3/' /etc/fail2ban/jail.local

# Install Geth
add-apt-repository -y ppa:ethereum/ethereum
apt update
apt install -y ethereum

# Create Geth systemd service
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

# Set up Geth data directory and log rotation
mkdir -p \$GETH_DATA_DIR
chown -R \$USERNAME:\$USERNAME \$GETH_DATA_DIR
cat > /etc/logrotate.d/geth <<EOLS
\$GETH_DATA_DIR/geth.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 \$USERNAME \$USERNAME
}
EOLS

# Set up backup script and cron job
mkdir -p \$BACKUP_DIR
cat > /usr/local/bin/backup-ethereum.sh <<EOLS
#!/bin/bash
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/ethereum_backup_\\\$TIMESTAMP.tar.gz"
systemctl stop geth
tar -czf \\\$BACKUP_FILE \$GETH_DATA_DIR
systemctl start geth
find \$BACKUP_DIR -type f -mtime +30 -delete
EOLS
chmod +x /usr/local/bin/backup-ethereum.sh
echo "0 3 * * * root /usr/local/bin/backup-ethereum.sh" >> /etc/crontab

# Enable and start services
systemctl enable geth prometheus prometheus-node-exporter grafana-server

# Install and configure Certbot
snap install core
snap refresh core
snap install --classic certbot
ln -s /snap/bin/certbot /usr/bin/certbot
certbot certonly --standalone -d \$DOMAIN --non-interactive --agree-tos -m \$EMAIL

# Set up Nginx as reverse proxy
apt install -y nginx
cat > /etc/nginx/sites-available/geth <<EOLS
server {
    listen 443 ssl;
    server_name \$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/\$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/\$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://localhost:8545;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_cache_bypass \\\$http_upgrade;
    }
}
EOLS
ln -s /etc/nginx/sites-available/geth /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Set up automatic SSL renewal
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | tee -a /etc/crontab > /dev/null

# Install and configure No-IP Dynamic Update Client (DUC)
echo "Installing No-IP Dynamic Update Client..."
cd /home/\$USERNAME
wget --content-disposition https://www.noip.com/download/linux/latest
tar xf noip-duc_*.tar.gz
cd noip-duc_*/binaries
apt install -y ./noip-duc_*_amd64.deb

# Configure No-IP DUC
echo "Configuring No-IP DUC..."
noip-duc -g all.ddnskey.com --username "\$NOIP_USERNAME" --password "\$NOIP_PASSWORD" --hostnames "\$DOMAIN" --daemon

# Create a systemd service for No-IP DUC
cat > /etc/systemd/system/noip-duc.service <<EOLS
[Unit]
Description=No-IP Dynamic Update Client
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/noip-duc -g all.ddnskey.com --username "\$NOIP_USERNAME" --password "\$NOIP_PASSWORD" --hostnames "\$DOMAIN" --daemon
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOLS

# Enable and start the No-IP DUC service
systemctl enable noip-duc.service
systemctl start noip-duc.service

# Attempt automatic port forwarding with UPnP
LOCAL_IP=\$(ip route get 1 | awk '{print \$7;exit}')
upnpc -a \$LOCAL_IP \$SSH_PORT \$SSH_PORT TCP
upnpc -a \$LOCAL_IP 80 80 TCP
upnpc -a \$LOCAL_IP 443 443 TCP
upnpc -a \$LOCAL_IP 30303 30303 TCP
upnpc -a \$LOCAL_IP 30303 30303 UDP

# Check if ports are accessible
check_port() {
    nc -z -w5 \$(curl -s https://api.ipify.org) \$1 >/dev/null 2>&1
    if [ \$? -eq 0 ]; then
        echo "Port \$1 is open"
    else
        echo "Port \$1 is not accessible. You may need to set up port forwarding manually."
    fi
}

check_port \$SSH_PORT
check_port 80
check_port 443
check_port 30303

echo "============================================================"
echo "IMPORTANT: Port Forwarding Instructions"
echo "============================================================"
echo "If any of the ports above are not accessible, you need to set up port forwarding on your Orbi RBR4 router:"
echo "1. Access your router's admin interface at http://orbilogin.com or http://192.168.1.1"
echo "2. Log in with your admin credentials"
echo "3. Go to Advanced > Advanced Setup > Port Forwarding / Port Triggering"
echo "4. Add port forwarding rules for the following ports:"
echo "   - SSH: \$SSH_PORT (TCP)"
echo "   - HTTP: 80 (TCP)"
echo "   - HTTPS: 443 (TCP)"
echo "   - Ethereum P2P: 30303 (TCP and UDP)"
echo "5. The internal IP address should be set to this machine's local IP address: \$LOCAL_IP"
echo "6. Save the settings and restart your router if required"
echo "============================================================"

# Secure sensitive information
chmod 600 /root/post_install.sh

# Clean up
apt clean
rm /root/post_install.sh

echo "Post-installation setup complete. Please reboot the system."
echo "IMPORTANT: Remember to change the password for user \$USERNAME after first login."
EOL

# Make the post-installation script executable
chmod +x "$MOUNT_POINT/root/post_install.sh"

# Chroot and run post-installation script
log_message "Entering chroot environment and running post-installation script..."
chroot "$MOUNT_POINT" /bin/bash -c "/root/post_install.sh"

# Unmount filesystems
log_message "Unmounting filesystems..."
umount -l "$MOUNT_POINT/proc"
umount -l "$MOUNT_POINT/sys"
umount -l "$MOUNT_POINT/dev"
umount -R "$MOUNT_POINT"

log_message "Installation complete. The system will now reboot."
reboot
